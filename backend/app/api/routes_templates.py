import os
import re
import subprocess
import tempfile
import base64
import uuid
import shutil
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from app.api.deps import get_current_user, get_current_user_optional
from app.db.models import User
from app.core.config import settings

router = APIRouter(prefix="/templates", tags=["templates"])

# 存储生成的图片
generated_images: Dict[str, bytes] = {}


def _transparent_png_bytes() -> bytes:
    # 1x1 transparent PNG
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/6X9lWQAAAAASUVORK5CYII="
    )


class TemplateInfo(BaseModel):
    id: str
    name: str
    category: str
    description: str
    thumbnail: Optional[str] = None
    has_data_file: bool = False
    data_files: List[str] = []


class DataFileInfo(BaseModel):
    name: str
    content: str
    path: str


class TemplateDetail(BaseModel):
    id: str
    name: str
    category: str
    code: str
    data_files: List[DataFileInfo] = []
    description: str


class RunRequest(BaseModel):
    code: str
    template_id: Optional[str] = None
    data_files: Optional[Dict[str, str]] = None


class RunResponse(BaseModel):
    success: bool
    image_base64: Optional[str] = None
    image_id: Optional[str] = None
    error: Optional[str] = None
    output: Optional[str] = None


def get_template_description(name: str, code: str = "") -> str:
    """Generate description from template name or code"""
    # 尝试从代码注释中提取描述
    if code:
        lines = code.split('\n')[:10]
        for line in lines:
            if line.strip().startswith('#') and len(line.strip()) > 5:
                desc = line.strip().lstrip('#').strip()
                if len(desc) > 5 and not desc.startswith('coding') and not desc.startswith('-*-'):
                    return desc[:100]
    
    # 根据名称生成描述
    name_clean = name.replace('.py', '').replace('_', ' ')
    return f"{name_clean} 绘图示例"


def scan_templates() -> List[TemplateInfo]:
    """Scan templates directory and return template info list
    
    新目录结构：
    图像代码数据汇总/
    ├── taylor/
    │   ├── 泰勒图示例/
    │   │   ├── main.py
    │   │   └── ...
    ├── scatter_cmap/
    │   ├── 模板1/
    │   │   ├── main.py
    │   │   └── ...
    ├── bar/
    ├── violin/
    └── ...
    """
    templates = []
    templates_path = settings.TEMPLATES_PATH
    
    # 调试日志
    import sys
    print(f"[DEBUG] TEMPLATES_PATH: {templates_path}", file=sys.stderr)
    print(f"[DEBUG] Path exists: {os.path.exists(templates_path)}", file=sys.stderr)
    
    if not os.path.exists(templates_path):
        return templates
    
    # 第一层：遍历图表类型目录（taylor, scatter_cmap, bar 等）
    for chart_type in os.listdir(templates_path):
        chart_type_path = os.path.join(templates_path, chart_type)
        
        # 跳过非目录、隐藏目录、脚本
        if not os.path.isdir(chart_type_path) or chart_type.startswith('.'):
            continue
        
        # 第二层：遍历每个图表类型下的模板目录
        for template_name in os.listdir(chart_type_path):
            template_dir = os.path.join(chart_type_path, template_name)
            
            if not os.path.isdir(template_dir):
                continue
            
            # 查找该模板目录下的 main.py（迁移脚本生成的标准文件）
            main_py_path = os.path.join(template_dir, 'main.py')
            
            if not os.path.exists(main_py_path):
                # 如果没有 main.py，尝试查找任何 .py 文件（兼容旧结构）
                py_files = [f for f in os.listdir(template_dir) 
                           if f.endswith('.py') and not f.startswith('__')]
                if not py_files:
                    continue
                # 选择名称最长的（通常最具描述性）
                main_py_path = os.path.join(template_dir, max(py_files, key=len))
            
            # 读取代码
            try:
                with open(main_py_path, 'r', encoding='utf-8') as f:
                    code = f.read()
            except Exception as e:
                print(f"[WARN] Failed to read {main_py_path}: {e}", file=sys.stderr)
                code = ""
            
            # 为该模板目录确保存在示范数据 Excel
            try:
                _ensure_demo_excel(template_dir, template_name, code)
            except Exception as e:
                print(f"[WARN] Failed to ensure demo excel for {template_dir}: {e}", file=sys.stderr)
            
            # 查找同目录下的数据文件
            data_files = []
            for df in os.listdir(template_dir):
                if df.endswith(('.csv', '.xlsx', '.xls')):
                    data_files.append(df)
            
            # 检查是否有缩略图
            thumbnail_rel = None
            
            # 1. 首先检查"图片实例"子文件夹
            thumb_dir = os.path.join(template_dir, '图片实例')
            if os.path.exists(thumb_dir):
                for img in os.listdir(thumb_dir):
                    if img.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                        thumb_path = os.path.join(thumb_dir, img)
                        thumbnail_rel = os.path.relpath(thumb_path, templates_path)
                        break
            
            # 2. 检查同级目录下的图片
            if not thumbnail_rel:
                for img in os.listdir(template_dir):
                    if img.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                        thumb_path = os.path.join(template_dir, img)
                        thumbnail_rel = os.path.relpath(thumb_path, templates_path)
                        break
            
            # 3. 递归检查子目录
            if not thumbnail_rel:
                for sub_root, sub_dirs, sub_files in os.walk(template_dir):
                    for img in sub_files:
                        if img.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                            thumb_path = os.path.join(sub_root, img)
                            thumbnail_rel = os.path.relpath(thumb_path, templates_path)
                            break
                    if thumbnail_rel:
                        break
            
            # 构建返回信息
            rel_path = os.path.relpath(main_py_path, templates_path)
            templates.append(TemplateInfo(
                id=rel_path,
                name=template_name,
                category=chart_type,  # 使用图表类型作为分类
                description=get_template_description(template_name, code),
                thumbnail=thumbnail_rel,
                has_data_file=len(data_files) > 0,
                data_files=data_files
            ))
    
    return templates


class ExcelParseResponse(BaseModel):
    headers: List[str]
    rows: List[dict]
    row_count: int


@router.post("/parse-excel", response_model=ExcelParseResponse)
async def parse_excel_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Parse Excel file and return headers and data rows"""
    import pandas as pd
    import io
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    filename = file.filename.lower()
    if not (filename.endswith('.xlsx') or filename.endswith('.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files (.xlsx, .xls) are supported")
    
    try:
        content = await file.read()
        df = pd.read_excel(io.BytesIO(content))
        
        # 转换为响应格式
        headers = df.columns.tolist()
        rows = df.to_dict(orient='records')
        
        # 限制行数避免过大
        max_rows = 1000
        if len(rows) > max_rows:
            rows = rows[:max_rows]
        
        return ExcelParseResponse(
            headers=headers,
            rows=rows,
            row_count=len(df)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse Excel: {str(e)}")



def _ensure_demo_excel(template_dir: str, template_name: str, code_text: str) -> str | None:
    # Ensure each template directory has a demo Excel file (for UI selection and plotting).
    # Returns demo filename if exists/created, else None.
    demo_filename = '示范数据.xlsx'
    demo_path = os.path.join(template_dir, demo_filename)
    if os.path.exists(demo_path):
        return demo_filename

    try:
        import pandas as pd
        import numpy as np

        name = (template_name or '')
        name_lower = name.lower()
        code_lower = (code_text or '').lower()

        # Taylor diagram demo
        if ('taylor' in code_lower) or ('泰勒' in name) or ('图7-4-2' in name):
            df = pd.DataFrame({
                '模型': ['PIR','NDIR','DIR','RIR','RIE','PIE','NDIE','DIE'],
                '相关系数': [0.95, 0.90, 0.88, 0.80, 0.70, 0.86, 0.84, 0.83],
                '标准差': [2.3, 2.4, 2.35, 2.1, 2.0, 2.6, 2.7, 3.2],
                '均方根误差': [1.55, 1.70, 1.72, 1.90, 2.00, 1.75, 1.78, 1.60],
            })
        # Scatter-compare demo (paired columns *_0, *_1)
        elif ('散点' in name) or ('对比' in name) or ('scatter' in name_lower) or ('compare' in name_lower):
            models = []
            for m in ['XGBoost','FCN','LSTM','CNN_LSTM','CNN-LSTM','CNNLSTM']:
                if m.lower() in name_lower:
                    models.append(m.replace('-', '_'))
            if not models:
                models = ['ModelA','ModelB','ModelC','ModelD']
            n = 200
            x = np.linspace(0, 100, n)
            data = {}
            for i, m in enumerate(models[:6]):
                # _0 as "True", _1 as "Pred"
                noise = (i + 1) * 2.0
                data[f'{m}_0'] = x
                data[f'{m}_1'] = x + np.sin(x/8.0) * noise
            df = pd.DataFrame(data)
        else:
            # Generic demo: 3 pairs
            n = 120
            x = np.linspace(0, 1, n)
            df = pd.DataFrame({
                'A_0': x * 100,
                'A_1': x * 100 + np.cos(x * 6) * 2,
                'B_0': x * 80,
                'B_1': x * 80 + np.sin(x * 5) * 3,
                'C_0': x * 60,
                'C_1': x * 60 + np.cos(x * 4) * 4,
            })

        df.to_excel(demo_path, index=False)
        return demo_filename
    except Exception:
        return None

@router.get("", response_model=List[TemplateInfo])
def list_templates(current_user: Optional[User] = Depends(get_current_user_optional)):
    """List all available templates (no auth required)"""
    templates = scan_templates()
    
    # 如果扫描不到模板，手动扫描一次（修复路径问题）
    if not templates:
        import os
        # 尝试多个可能的路径
        possible_paths = [
            r"D:\文件夹\绘图\图像代码数据汇总",
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "图像代码数据汇总"),
            "图像代码数据汇总"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                # 临时修改settings
                settings.TEMPLATES_ROOT = path
                templates = scan_templates()
                if templates:
                    break
    
    return templates


# 静态图片访问端点 - 无需认证，允许 <img> 标签直接访问
# 必须在 /{template_id:path} 之前定义
@router.get("/image/{image_path:path}")
def get_template_image(image_path: str):
    """Get any image from templates directory (public access for thumbnails)"""
    templates_path = settings.TEMPLATES_PATH
    file_path = os.path.join(templates_path, image_path)
    
    # 安全检查 - 防止路径遍历攻击
    real_path = os.path.realpath(file_path)
    templates_real = os.path.realpath(templates_path)
    if not real_path.startswith(templates_real):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    # 检查是否是图片文件
    if not file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        raise HTTPException(status_code=400, detail="Not an image file")
    
    return FileResponse(file_path)


@router.get("/{template_id:path}/thumbnail")
def get_template_thumbnail(template_id: str):
    """Get template thumbnail image (public access)"""
    templates_path = settings.TEMPLATES_PATH
    file_path = os.path.join(templates_path, template_id)
    
    # 安全检查
    real_path = os.path.realpath(file_path)
    templates_real = os.path.realpath(templates_path)
    if not real_path.startswith(templates_real):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 查找缩略图
    parent_dir = os.path.dirname(file_path)
    
    # 1. 首先检查"图片实例"子文件夹
    thumb_dir = os.path.join(parent_dir, '图片实例')
    if os.path.exists(thumb_dir):
        for img in os.listdir(thumb_dir):
            if img.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                return FileResponse(os.path.join(thumb_dir, img))
    
    # 2. 检查同级目录下的图片
    for img in os.listdir(parent_dir):
        if img.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            return FileResponse(os.path.join(parent_dir, img))
    
    # 3. 递归检查子目录
    for sub_root, sub_dirs, sub_files in os.walk(parent_dir):
        for img in sub_files:
            if img.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                return FileResponse(os.path.join(sub_root, img))
    
    # 没有缩略图：返回占位图，避免前端出现破图与大量 404
    return Response(content=_transparent_png_bytes(), media_type="image/png")


@router.get("/{template_id:path}", response_model=TemplateDetail)
def get_template_detail(template_id: str, current_user: User = Depends(get_current_user)):
    """Get template detail with code and data files"""
    templates_path = settings.TEMPLATES_PATH
    file_path = os.path.join(templates_path, template_id)
    
    # 安全检查
    real_path = os.path.realpath(file_path)
    templates_real = os.path.realpath(templates_path)
    if not real_path.startswith(templates_real):
        raise HTTPException(status_code=403, detail="Access denied")
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Template not found")
    
    # 读取代码
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read template: {e}")
    
    # 读取数据文件
    parent_dir = os.path.dirname(file_path)

    # 确保每个模板目录下都有一个“示范数据.xlsx”（用于演示数据格式；可直接选取绘图）
    try:
        _ensure_demo_excel(parent_dir, os.path.basename(parent_dir), code)
    except Exception:
        pass

    data_files = []

    # 说明：
    # - 对 CSV：返回文本内容，前端可直接解析
    # - 对 Excel：返回“预览用 CSV 文本”（由 Excel 转换），便于前端解析列
    #   但运行时后端不会用该文本覆盖原始 .xlsx 文件（run 接口会跳过写入 .xlsx/.xls），
    #   Python 脚本将从模板目录拷贝到临时目录的真实 Excel 读取。
    import pandas as pd

    def _append_data_file(df_name: str):
        df_path = os.path.join(parent_dir, df_name)
        if not os.path.isfile(df_path):
            return
        lower = df_name.lower()
        if not (lower.endswith('.csv') or lower.endswith('.xlsx') or lower.endswith('.xls')):
            return

        content = ''
        try:
            if lower.endswith('.csv'):
                with open(df_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                try:
                    preview_df = pd.read_excel(df_path)
                    # 限制预览行数，避免前端/接口过大
                    content = preview_df.head(200).to_csv(index=False)
                except Exception:
                    content = "[Excel文件，无法预览]"
        except Exception:
            content = "[读取文件失败]"

        data_files.append(DataFileInfo(
            name=df_name,
            content=content,
            path=os.path.join(template_id.split(os.sep)[0], os.path.basename(parent_dir), df_name)
        ))

    # 让示范数据优先出现在下拉框（前端默认取第一个）
    demo_name = '示范数据.xlsx'
    names = []
    try:
        names = os.listdir(parent_dir)
    except Exception:
        names = []

    if demo_name in names:
        _append_data_file(demo_name)

    for df_name in names:
        if df_name == demo_name:
            continue
        _append_data_file(df_name)

    # 获取分类和名称
    parts = template_id.split(os.sep)
    if len(parts) == 0:
        parts = template_id.split('/')
    category = parts[0] if len(parts) > 0 else "未分类"
    template_name = os.path.basename(parent_dir)
    if template_name == category:
        template_name = os.path.basename(file_path).replace('.py', '')

    # 为每个模板目录确保存在一个示范数据 Excel（用于下拉选择与格式演示）
    _ensure_demo_excel(parent_dir, template_name, code)

    # 重新排序：示范数据.xlsx 优先
    try:
        demo_first = []
        others = []
        for item in data_files:
            if item.name == '示范数据.xlsx':
                demo_first.append(item)
            else:
                others.append(item)
        data_files = demo_first + others
    except Exception:
        pass

    return TemplateDetail(
        id=template_id,
        name=template_name,
        category=category,
        code=code,
        data_files=data_files,
        description=get_template_description(template_name, code)
    )


@router.post("/run", response_model=RunResponse)
def run_template(request: RunRequest):
    """Execute Python code and return the generated image"""
    import textwrap

    with tempfile.TemporaryDirectory() as tmpdir:
        # 如果有模板ID，复制数据文件到临时目录
        if request.template_id:
            templates_path = settings.TEMPLATES_PATH
            template_path = os.path.join(templates_path, request.template_id)
            if os.path.exists(template_path):
                parent_dir = os.path.dirname(template_path)
                for f in os.listdir(parent_dir):
                    if f.endswith(('.csv', '.xlsx', '.xls', '.png', '.jpg')):
                        src = os.path.join(parent_dir, f)
                        dst = os.path.join(tmpdir, f)
                        shutil.copy2(src, dst)
        
        # 如果有自定义数据文件内容，写入临时目录
        if request.data_files:
            for name, content_b64 in request.data_files.items():
                try:
                    # 1. 解码 Base64
                    if "," in content_b64:
                        content_b64 = content_b64.split(",")[1]
                    file_content = base64.b64decode(content_b64)
                    
                    # 2. 获取文件路径
                    file_path = os.path.join(tmpdir, name)
                    
                    # --- [修改点]：削除了之前的 .xlsx 检查，允许覆盖任何文件 ---
                    # 直接写入二进制内容
                    with open(file_path, 'wb') as f:
                        f.write(file_content)
                    print(f"已写入文件: {name}, 大小: {len(file_content)} bytes")
                    
                except Exception as e:
                    print(f"写入文件 {name} 失败: {e}")
                    # 继续处理其他文件，不要直接崩溃
                    continue
        
        # 准备执行代码
        output_path = os.path.join(tmpdir, 'output.png')
        
        # 清理用户代码缩进（避免顶层意外缩进导致 IndentationError）
        cleaned_code = textwrap.dedent(request.code or "").strip("\n")

        # 包装代码
        wrapper_code = f'''
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

import os
os.chdir(r"{tmpdir}")

{cleaned_code}

# 保存图片
if plt.get_fignums():
    plt.savefig(r"{output_path}", dpi=150, bbox_inches='tight', facecolor='white')
    plt.close('all')
'''
        
        script_path = os.path.join(tmpdir, 'script.py')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(wrapper_code)
        
        # 使用当前 Python 解释器执行脚本（确保使用同一环境的依赖）
        import sys
        python_executable = sys.executable
        
        # 准备环境变量，修复 Python 3.14 的路径问题
        env = os.environ.copy()
        env['MPLCONFIGDIR'] = tmpdir
        # 移除可能导致问题的环境变量
        env.pop('PYTHONHOME', None)
        env.pop('__PYVENV_LAUNCHER__', None)
        
        # 执行脚本
        try:
            result = subprocess.run(
                [python_executable, script_path],
                capture_output=True,
                text=True,
                timeout=180,
                cwd=tmpdir,
                env=env
            )
            
            output = result.stdout
            error = result.stderr if result.returncode != 0 else None
            
            # 检查是否生成了图片
            if os.path.exists(output_path):
                with open(output_path, 'rb') as f:
                    image_data = f.read()
                
                image_id = str(uuid.uuid4())
                generated_images[image_id] = image_data
                
                return RunResponse(
                    success=True,
                    image_base64=base64.b64encode(image_data).decode('utf-8'),
                    image_id=image_id,
                    output=output
                )
            else:
                return RunResponse(
                    success=False,
                    error=error or "未生成图片，请检查代码是否包含 plt.show()，或是否在脚本中保存图片。",
                    output=output
                )
                
        except subprocess.TimeoutExpired:
            return RunResponse(
                success=False,
                error="执行超时（120秒限制）"
            )
        except Exception as e:
            return RunResponse(
                success=False,
                error=str(e)
            )


@router.get("/image/{image_id}")
def get_image(image_id: str, current_user: User = Depends(get_current_user)):
    """Get generated image by ID"""
    if image_id not in generated_images:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return Response(
        content=generated_images[image_id],
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename={image_id}.png"}
    )


@router.post("/run-with-files", response_model=RunResponse)
async def run_template_with_files(
    code: str = Form(...),
    template_id: Optional[str] = Form(None),
    data_files_json: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Execute code with uploaded files"""
    import json
    
    data_files = {}
    if data_files_json:
        try:
            data_files = json.loads(data_files_json)
        except:
            pass
    
    request = RunRequest(code=code, template_id=template_id, data_files=data_files)
    return run_template(request, current_user)
