"""Template scan & isolated run APIs.

Phase 2 (The Brain):
- scan_templates(): recursively scan `图像代码数据汇总` and derive category/tags from folder structure
- GET  /api/templates/list: return templates + a simple tree structure
- POST /api/templates/run : accept uploaded CSV/Excel, execute the target template in a temp folder, return output image
- POST /api/templates/parse-data : parse uploaded data file, return column info and preview
- POST /api/templates/run-configured : run template with custom chart configuration

Notes:
- The templates are intended to be standardized by `scripts/standardize_templates.py` (Phase 1)
  so that they (1) use Agg backend, (2) handle Chinese fonts, (3) auto-discover uploaded data file(s),
  (4) save to output.png.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from app.api.deps import get_current_user_optional
from app.core.config import settings
from app.db.models import User


router = APIRouter(prefix="/templates", tags=["templates"])


class TemplateMeta(BaseModel):
    id: str
    name: str
    category: str
    tags: List[str] = []
    rel_dir: str
    rel_main: str
    thumbnail: Optional[str] = None


class TemplateTreeNode(BaseModel):
    name: str
    path: str
    type: str  # 'folder' | 'template'
    children: List["TemplateTreeNode"] = []
    template_id: Optional[str] = None


TemplateTreeNode.model_rebuild()


class TemplatesListResponse(BaseModel):
    root: str
    templates: List[TemplateMeta]
    tree: TemplateTreeNode


def _templates_root() -> Path:
    return Path(settings.TEMPLATES_PATH).resolve()


def _safe_path_under_root(rel: str) -> Path:
    root = _templates_root()
    candidate = (root / rel).resolve()
    if root not in candidate.parents and candidate != root:
        raise HTTPException(status_code=403, detail="Access denied")
    return candidate


def _find_thumbnail(template_dir: Path, root: Path) -> Optional[str]:
    """Best-effort thumbnail discovery; returned as posix relative path."""
    # Prefer: 图片实例/*.(png|jpg)
    img_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp"}
    preferred_dirs = [template_dir / "图片实例", template_dir]

    for d in preferred_dirs:
        if not d.exists() or not d.is_dir():
            continue
        for p in sorted(d.iterdir()):
            if p.is_file() and p.suffix.lower() in img_exts:
                return p.relative_to(root).as_posix()

    # Fallback: recursive search (first match)
    for p in template_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in img_exts:
            return p.relative_to(root).as_posix()

    return None


def scan_templates() -> List[TemplateMeta]:
    """Recursively scan templates root for any folder containing main.py."""
    root = _templates_root()
    if not root.exists():
        return []

    templates: List[TemplateMeta] = []

    for main_py in root.rglob("main.py"):
        if not main_py.is_file():
            continue
        # Skip hidden folders
        if any(part.startswith(".") for part in main_py.relative_to(root).parts):
            continue

        rel_main = main_py.relative_to(root).as_posix()
        rel_dir = main_py.parent.relative_to(root).as_posix()
        parts = list(main_py.parent.relative_to(root).parts)

        # Folder-structure -> category/tags
        category = parts[0] if parts else "未分类"
        name = parts[-1] if parts else "root"
        tags = parts[1:-1] if len(parts) >= 3 else []

        templates.append(
            TemplateMeta(
                id=rel_main,
                name=name,
                category=category,
                tags=tags,
                rel_dir=rel_dir,
                rel_main=rel_main,
                thumbnail=_find_thumbnail(main_py.parent, root),
            )
        )

    # stable ordering: category/path
    templates.sort(key=lambda t: (t.category, t.rel_dir, t.name))
    return templates


def _build_tree(templates: List[TemplateMeta]) -> TemplateTreeNode:
    root_node = TemplateTreeNode(name="图像代码数据汇总", path="", type="folder", children=[])

    # A simple trie by folder segments
    def find_or_create_child(parent: TemplateTreeNode, name: str, path: str) -> TemplateTreeNode:
        for c in parent.children:
            if c.type == "folder" and c.name == name:
                return c
        node = TemplateTreeNode(name=name, path=path, type="folder", children=[])
        parent.children.append(node)
        parent.children.sort(key=lambda n: (n.type != "folder", n.name))
        return node

    for t in templates:
        segs = [s for s in t.rel_dir.split("/") if s]
        parent = root_node
        current_path = ""
        for s in segs:
            current_path = f"{current_path}/{s}".lstrip("/")
            parent = find_or_create_child(parent, s, current_path)

        # Add template leaf
        parent.children.append(
            TemplateTreeNode(
                name=t.name,
                path=t.rel_dir,
                type="template",
                children=[],
                template_id=t.id,
            )
        )
        parent.children.sort(key=lambda n: (n.type != "folder", n.name))

    return root_node


@router.get("/list", response_model=TemplatesListResponse)
def list_templates_structured(current_user: Optional[User] = Depends(get_current_user_optional)):
    templates = scan_templates()
    root = _templates_root()
    return TemplatesListResponse(
        root=str(root),
        templates=templates,
        tree=_build_tree(templates),
    )


# Backward-compatible alias for existing UI: GET /api/templates
@router.get("", response_model=List[TemplateMeta])
def list_templates_flat(current_user: Optional[User] = Depends(get_current_user_optional)):
    return scan_templates()


# Static image endpoint for thumbnails - must be before dynamic routes
@router.get("/image/{image_path:path}")
def get_template_image(image_path: str):
    """Get any image from templates directory (public access for thumbnails)"""
    root = _templates_root()
    file_path = root / image_path
    
    # Security check - prevent path traversal
    try:
        file_path = file_path.resolve()
        if root not in file_path.parents and file_path != root:
            raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path")
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Check if it's an image file
    if file_path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".gif", ".bmp"}:
        raise HTTPException(status_code=400, detail="Not an image file")
    
    return FileResponse(file_path)


@router.post("/run")
async def run_template(
    template_id: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Run a template in an isolated temp directory and return output.png.

    - template_id: relative path to the template's main.py, as returned by /list
    - files: one or more uploaded data files (.csv/.xlsx/.xls)
    """
    if not files:
        raise HTTPException(status_code=400, detail="No data files uploaded")

    allowed = {".csv", ".xlsx", ".xls"}
    for f in files:
        if not f.filename:
            raise HTTPException(status_code=400, detail="Uploaded file missing filename")
        ext = Path(f.filename).suffix.lower()
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # Resolve template path safely
    main_py = _safe_path_under_root(template_id)
    if not main_py.exists() or not main_py.is_file() or main_py.name.lower() != "main.py":
        raise HTTPException(status_code=404, detail="Template main.py not found")

    with tempfile.TemporaryDirectory(prefix="echarts_lab_") as tmpdir:
        tmp = Path(tmpdir)

        # Copy main.py into isolated folder
        shutil.copy2(main_py, tmp / "main.py")

        # Save uploaded files into isolated folder (CWD)
        for uf in files:
            content = await uf.read()
            (tmp / uf.filename).write_bytes(content)

        output_path = tmp / "output.png"

        env = os.environ.copy()
        env["MPLBACKEND"] = "Agg"
        env["MPLCONFIGDIR"] = str(tmp)
        env["PYTHONUTF8"] = "1"
        env.pop("PYTHONHOME", None)
        env.pop("__PYVENV_LAUNCHER__", None)

        try:
            proc = subprocess.run(
                [sys.executable, "main.py"],
                cwd=str(tmp),
                env=env,
                capture_output=True,
                text=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=408, detail="Template execution timed out (180s)")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start template: {e}")

        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            stdout = (proc.stdout or "").strip()
            msg = stderr or stdout or "Template execution failed"
            # Keep detail reasonably sized
            if len(msg) > 4000:
                msg = msg[:4000] + "..."
            raise HTTPException(status_code=400, detail=msg)

        if not output_path.exists():
            # Fallback: find any png in temp dir
            pngs = sorted(tmp.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            if pngs:
                output_path = pngs[0]
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No output image produced. Expecting output.png (run Phase 1 standardizer first).",
                )

        img = output_path.read_bytes()
        return Response(content=img, media_type="image/png")


# ============================================================================
# Data Parsing API - parse uploaded file to get column info
# ============================================================================

class ColumnInfo(BaseModel):
    name: str
    dtype: str
    sample_values: List[Any]
    is_numeric: bool
    unique_count: int


class DataParseResponse(BaseModel):
    filename: str
    row_count: int
    columns: List[ColumnInfo]
    preview: List[Dict[str, Any]]  # First 10 rows


@router.post("/parse-data", response_model=DataParseResponse)
async def parse_data_file(
    file: UploadFile = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Parse uploaded data file and return column information."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")
    
    ext = Path(file.filename).suffix.lower()
    allowed = {".csv", ".xlsx", ".xls"}
    if ext not in allowed:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")
    
    content = await file.read()
    
    try:
        if ext == ".csv":
            # Try multiple encodings
            for encoding in ["utf-8", "gbk", "gb2312", "latin1"]:
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                df = pd.read_csv(io.BytesIO(content), encoding="utf-8", errors="replace")
        else:
            df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
    
    columns = []
    for col in df.columns:
        is_numeric = pd.api.types.is_numeric_dtype(df[col])
        sample = df[col].dropna().head(5).tolist()
        # Convert numpy types to native Python types for JSON serialization
        sample = [float(v) if isinstance(v, (int, float)) and pd.notna(v) else str(v) for v in sample]
        
        columns.append(ColumnInfo(
            name=str(col),
            dtype=str(df[col].dtype),
            sample_values=sample,
            is_numeric=is_numeric,
            unique_count=int(df[col].nunique()),
        ))
    
    # Preview data (first 10 rows)
    preview_df = df.head(10).fillna("")
    preview = []
    for _, row in preview_df.iterrows():
        row_dict = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                row_dict[str(col)] = ""
            elif isinstance(val, (int, float)):
                row_dict[str(col)] = float(val) if isinstance(val, float) else int(val)
            else:
                row_dict[str(col)] = str(val)
        preview.append(row_dict)
    
    return DataParseResponse(
        filename=file.filename,
        row_count=len(df),
        columns=columns,
        preview=preview,
    )


# ============================================================================
# Configured Template Run API - run with custom chart settings
# ============================================================================

class ChartConfig(BaseModel):
    """Chart configuration for customized rendering."""
    # Data mapping
    x_column: Optional[str] = None
    y_columns: Optional[List[str]] = None
    group_column: Optional[str] = None
    selected_pairs: Optional[List[str]] = None  # 选中的模型配对名称
    
    # Visual style
    marker_style: str = "circle"  # circle, square, diamond, triangle, star
    marker_size: int = 8
    line_style: str = "solid"  # solid, dashed, dotted
    line_width: float = 1.5
    
    # Colors (hex strings)
    colors: Optional[List[str]] = None
    colormap: str = "jet"
    
    # Layout
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    show_legend: bool = True
    show_grid: bool = True
    
    # Figure size
    fig_width: float = 10.0
    fig_height: float = 8.0
    dpi: int = 150
    
    # 柱形图专属配置
    show_points: bool = True       # 是否显示数据点
    show_error: bool = True        # 是否显示误差线
    error_type: str = "sd"         # 误差类型: sd, se, ci
    bar_width: float = 0.8         # 柱子宽度
    point_size: int = 5            # 数据点大小
    
    # 云雨图/小提琴图专属配置
    raincloud_style: int = 1       # 云雨图样式 1-6
    show_box: bool = True          # 是否显示箱线图
    
    # 子图模板专属配置
    n_subplots: int = 2            # 子图数量
    subplot_layout: str = "vertical"  # 子图布局: vertical, horizontal
    show_colorbar: bool = True     # 显示colorbar
    share_colorbar: bool = True    # 共享colorbar
    
    # 三元图专属配置
    ternary_mode: str = "group"    # 三元图模式: group, color
    z_label: str = "Variable 3"    # 第三个轴标签
    
    # 模型预测对比图专属配置
    true_color: str = "#0000FF"    # 真实值颜色
    pred_color: str = "#FF0000"    # 预测值颜色
    show_metrics: bool = True      # 显示R²和MAE指标
    invert_y: bool = True          # Y轴反向
    
    # 堆积柱形图专属配置
    show_values: bool = True       # 显示数值标签
    
    # 相关性散点图专属配置
    show_regression: bool = True   # 显示回归线和方程
    show_r2: bool = True           # 显示R²值
    show_diagonal: bool = True     # 显示1:1对角线
    
    # 矩阵气泡图专属配置
    bubble_shape: str = "circle"   # 气泡形状: circle, square
    show_size_legend: bool = True  # 显示大小图例
    bubble_alpha: float = 0.9      # 气泡透明度
    
    # 泰勒图专属配置
    show_rmsd: bool = True         # 显示RMSD等值线
    show_labels: bool = True       # 显示数据点标签
    use_different_markers: bool = True  # 使用不同标记区分模型
    ref_std: float = 5.0           # 参考标准差
    
    # 三元密度图专属配置
    show_scatter: bool = True      # 显示散点
    scatter_color: str = "#1f4e79" # 散点颜色
    colorbar_position: str = "right"  # 颜色条位置: right, bottom
    density_sigma: float = 2.0     # 密度平滑系数
    
    # 通用热力图专属配置
    heatmap_mode: str = "correlation"  # 热力图模式: correlation, matrix
    square_cells: bool = True      # 正方形单元格
    center_zero: bool = True       # 颜色中心为0
    value_format: str = ".2f"      # 数值格式
    font_size: int = 10            # 数值字体大小
    
    # 显著性箱线图专属配置
    test_method: str = "mww"       # 检验方法: ttest, mww
    show_significance: bool = True # 显示显著性标注
    box_width: float = 0.6         # 箱子宽度
    point_alpha: float = 0.7       # 散点透明度
    jitter_amount: float = 0.15    # 散点抖动量
    
    # 通用箱线图专属配置
    box_alpha: float = 0.8         # 箱子透明度
    show_outliers: bool = True     # 显示异常值
    show_notch: bool = False       # 显示缺口
    show_means: bool = False       # 显示均值
    median_width: float = 2.0      # 中位数线宽度
    orient: str = "vertical"       # 方向: vertical, horizontal
    
    # 边际组合图/相关性矩阵图专属配置
    matrix_style: str = "circle"   # 矩阵样式: circle, square, heatmap, values
    display_mode: str = "full"     # 显示模式: full, lower, upper
    grid_width: float = 1.5        # 网格线宽


# Generate Python code for chart configuration
def _generate_config_code(config: ChartConfig) -> str:
    """Generate Python code that sets up chart configuration."""
    marker_map = {
        "circle": "o",
        "square": "s",
        "diamond": "D",
        "triangle": "^",
        "star": "*",
        "plus": "+",
        "x": "x",
    }
    
    line_map = {
        "solid": "-",
        "dashed": "--",
        "dotted": ":",
        "dashdot": "-.",
    }
    
    colors_str = "None"
    if config.colors:
        colors_str = repr(config.colors)
    
    y_cols_str = "None"
    if config.y_columns:
        y_cols_str = repr(config.y_columns)
    
    selected_pairs_str = "None"
    if config.selected_pairs:
        selected_pairs_str = repr(config.selected_pairs)
    
    code = f'''
# ========== Chart Configuration (Auto-generated) ==========
import json as _json

class ChartConfig:
    x_column = {repr(config.x_column)}
    y_columns = {y_cols_str}
    group_column = {repr(config.group_column)}
    selected_pairs = {selected_pairs_str}
    
    marker_style = "{marker_map.get(config.marker_style, 'o')}"
    marker_size = {config.marker_size}
    line_style = "{line_map.get(config.line_style, '-')}"
    line_width = {config.line_width}
    
    colors = {colors_str}
    colormap = "{config.colormap}"
    
    title = {repr(config.title)}
    x_label = {repr(config.x_label)}
    y_label = {repr(config.y_label)}
    show_legend = {config.show_legend}
    show_grid = {config.show_grid}
    
    fig_width = {config.fig_width}
    fig_height = {config.fig_height}
    dpi = {config.dpi}
    
    # 柱形图专属配置
    show_points = {config.show_points}
    show_error = {config.show_error}
    error_type = "{config.error_type}"
    bar_width = {config.bar_width}
    point_size = {config.point_size}
    
    # 云雨图/小提琴图专属配置
    raincloud_style = {config.raincloud_style}
    show_box = {config.show_box}
    
    # 子图模板专属配置
    n_subplots = {config.n_subplots}
    subplot_layout = "{config.subplot_layout}"
    show_colorbar = {config.show_colorbar}
    share_colorbar = {config.share_colorbar}
    
    # 三元图专属配置
    ternary_mode = "{config.ternary_mode}"
    z_label = {repr(config.z_label)}
    
    # 模型预测对比图专属配置
    true_color = "{config.true_color}"
    pred_color = "{config.pred_color}"
    show_metrics = {config.show_metrics}
    invert_y = {config.invert_y}
    
    # 堆积柱形图专属配置
    show_values = {config.show_values}
    
    # 相关性散点图专属配置
    show_regression = {config.show_regression}
    show_r2 = {config.show_r2}
    show_diagonal = {config.show_diagonal}
    
    # 矩阵气泡图专属配置
    marker_style = "{config.bubble_shape}"
    show_size_legend = {config.show_size_legend}
    bubble_alpha = {config.bubble_alpha}
    
    # 泰勒图专属配置
    show_rmsd = {config.show_rmsd}
    show_labels = {config.show_labels}
    use_different_markers = {config.use_different_markers}
    ref_std = {config.ref_std}
    
    # 三元密度图专属配置
    show_scatter = {config.show_scatter}
    scatter_color = "{config.scatter_color}"
    colorbar_position = "{config.colorbar_position}"
    density_sigma = {config.density_sigma}
    
    # 通用热力图专属配置
    heatmap_mode = "{config.heatmap_mode}"
    square_cells = {config.square_cells}
    center_zero = {config.center_zero}
    value_format = "{config.value_format}"
    font_size = {config.font_size}
    
    # 显著性箱线图专属配置
    test_method = "{config.test_method}"
    show_significance = {config.show_significance}
    box_width = {config.box_width}
    point_alpha = {config.point_alpha}
    jitter_amount = {config.jitter_amount}
    
    # 通用箱线图专属配置
    box_alpha = {config.box_alpha}
    show_outliers = {config.show_outliers}
    show_notch = {config.show_notch}
    show_means = {config.show_means}
    median_width = {config.median_width}
    orient = "{config.orient}"
    
    # 边际组合图/相关性矩阵图专属配置
    matrix_style = "{config.matrix_style}"
    display_mode = "{config.display_mode}"
    grid_width = {config.grid_width}

# Make config available as global
CHART_CONFIG = ChartConfig()
# ========== End Configuration ==========

'''
    return code


@router.post("/run-configured")
async def run_template_configured(
    template_id: str = Form(...),
    config: str = Form("{}"),  # JSON string of ChartConfig
    files: List[UploadFile] = File(...),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Run a template with custom chart configuration.
    
    - template_id: relative path to the template's main.py
    - config: JSON string containing ChartConfig fields
    - files: one or more uploaded data files (.csv/.xlsx/.xls)
    """
    if not files:
        raise HTTPException(status_code=400, detail="No data files uploaded")

    allowed = {".csv", ".xlsx", ".xls"}
    for f in files:
        if not f.filename:
            raise HTTPException(status_code=400, detail="Uploaded file missing filename")
        ext = Path(f.filename).suffix.lower()
        if ext not in allowed:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # Parse config
    try:
        config_dict = json.loads(config)
        chart_config = ChartConfig(**config_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid config: {str(e)}")

    # Resolve template path safely
    main_py = _safe_path_under_root(template_id)
    if not main_py.exists() or not main_py.is_file() or main_py.name.lower() != "main.py":
        raise HTTPException(status_code=404, detail="Template main.py not found")

    with tempfile.TemporaryDirectory(prefix="echarts_lab_") as tmpdir:
        tmp = Path(tmpdir)

        # Read original main.py and remove BOM if present
        original_code = main_py.read_text(encoding="utf-8-sig")
        
        # Prepend config code
        config_code = _generate_config_code(chart_config)
        modified_code = config_code + original_code
        
        # Write modified main.py without BOM
        (tmp / "main.py").write_text(modified_code, encoding="utf-8")

        # Save uploaded files into isolated folder (CWD)
        for uf in files:
            content = await uf.read()
            (tmp / uf.filename).write_bytes(content)

        # Also save the config as JSON for templates that want to read it directly
        (tmp / "_chart_config.json").write_text(json.dumps(config_dict, ensure_ascii=False, indent=2), encoding="utf-8")

        output_path = tmp / "output.png"

        env = os.environ.copy()
        env["MPLBACKEND"] = "Agg"
        env["MPLCONFIGDIR"] = str(tmp)
        env["PYTHONUTF8"] = "1"
        env.pop("PYTHONHOME", None)
        env.pop("__PYVENV_LAUNCHER__", None)

        try:
            proc = subprocess.run(
                [sys.executable, "main.py"],
                cwd=str(tmp),
                env=env,
                capture_output=True,
                text=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=408, detail="Template execution timed out (180s)")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start template: {e}")

        if proc.returncode != 0:
            stderr = (proc.stderr or "").strip()
            stdout = (proc.stdout or "").strip()
            msg = stderr or stdout or "Template execution failed"
            if len(msg) > 4000:
                msg = msg[:4000] + "..."
            raise HTTPException(status_code=400, detail=msg)

        if not output_path.exists():
            pngs = sorted(tmp.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            if pngs:
                output_path = pngs[0]
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No output image produced. Expecting output.png.",
                )

        img = output_path.read_bytes()
        return Response(content=img, media_type="image/png")

