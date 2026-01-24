# 矩阵气泡图
# 支持多种形状标记（圆形/方形/菱形/三角形）、大小映射、颜色映射
import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# 预设配色方案
# ============================================================================
COLOR_PALETTES = {
    'jet': plt.cm.jet,
    'viridis': plt.cm.viridis,
    'plasma': plt.cm.plasma,
    'coolwarm': plt.cm.coolwarm,
    'RdYlBu': plt.cm.RdYlBu_r,
    'hot': plt.cm.hot,
}

# ============================================================================
# 读取配置
# ============================================================================
def get_config():
    """获取图表配置"""
    default = {
        'colormap': 'jet',
        'colors': None,
        'title': '',
        'x_label': '',
        'y_label': '',
        'show_legend': True,
        'show_grid': True,
        'line_style': 'solid',       # 网格线样式: solid, dashed, dotted, none
        'fig_width': 10,
        'fig_height': 8,
        'dpi': 150,
        'marker_size': 100,
        # 矩阵气泡图专属配置
        'marker_style': 'circle',    # circle, square, diamond, triangle
        'show_size_legend': True,    # 显示大小图例
        'show_colorbar': True,       # 显示颜色条
        'bubble_alpha': 0.9,         # 气泡透明度
    }
    
    # 从 CHART_CONFIG 读取
    try:
        cfg = CHART_CONFIG
        for k in default:
            val = getattr(cfg, k, None)
            if val is not None:
                default[k] = val
    except NameError:
        # 从 JSON 文件读取
        if os.path.exists('_chart_config.json'):
            try:
                with open('_chart_config.json', 'r', encoding='utf-8') as f:
                    cfg_json = json.load(f)
                    for k in default:
                        if k in cfg_json and cfg_json[k] is not None:
                            default[k] = cfg_json[k]
            except Exception:
                pass
    
    return default

config = get_config()
print(f"配置: colormap={config['colormap']}, marker_style={config.get('marker_style', 'circle')}")

# ============================================================================
# 加载数据
# ============================================================================
def load_data():
    """智能查找并加载数据文件"""
    files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    files = [f for f in files if not f.startswith('_')]
    
    if not files:
        # 内置示例数据 - 模拟图片中的数据结构
        np.random.seed(42)
        rows = [f'c{i}' for i in range(1, 9)]  # c1-c8
        cols = [f'g{i}' for i in range(1, 11)]  # g1-g10
        
        # 生成Value（颜色映射）和Size（大小映射）
        n_rows, n_cols = len(rows), len(cols)
        values = np.random.uniform(52, 150, (n_rows, n_cols))
        sizes = np.random.uniform(75, 150, (n_rows, n_cols))
        
        # 创建长格式数据
        data = []
        for i, row in enumerate(rows):
            for j, col in enumerate(cols):
                data.append({
                    'Row': row,
                    'Col': col,
                    'Value': values[i, j],
                    'Size': sizes[i, j]
                })
        return pd.DataFrame(data)
    
    target = files[0]
    print(f"加载数据: {target}")
    
    if target.endswith('.csv'):
        for enc in ['utf-8', 'gbk', 'gb2312', 'latin1']:
            try:
                return pd.read_csv(target, encoding=enc)
            except:
                continue
        return pd.read_csv(target, encoding='utf-8', errors='replace')
    else:
        return pd.read_excel(target)

df = load_data()
print(f"数据: {len(df)} 行, {len(df.columns)} 列")
print(f"列名: {list(df.columns)}")

# ============================================================================
# 解析数据格式
# ============================================================================
# 支持两种数据格式：
# 1. 长格式：Row, Col, Value, Size
# 2. 矩阵格式：第一列为行标签，其他列为数值

def parse_data(df):
    """解析数据，返回行标签、列标签、值矩阵、大小矩阵"""
    cols = df.columns.tolist()
    
    # 检测是否是长格式（有Row, Col, Value列）
    has_row = any('row' in c.lower() or '行' in c for c in cols)
    has_col = any('col' in c.lower() or '列' in c for c in cols)
    has_value = any('value' in c.lower() or '值' in c.lower() or 'color' in c.lower() for c in cols)
    
    if has_row and has_col and has_value:
        # 长格式
        row_col = None
        col_col = None
        value_col = None
        size_col = None
        
        for c in cols:
            cl = c.lower()
            if 'row' in cl or '行' in c:
                row_col = c
            elif 'col' in cl or '列' in c:
                col_col = c
            elif 'size' in cl or '大小' in c:
                size_col = c
            elif 'value' in cl or '值' in c or 'color' in cl:
                value_col = c
        
        # 如果没找到value列，使用第一个数值列
        if not value_col:
            for c in cols:
                if pd.api.types.is_numeric_dtype(df[c]) and c != size_col:
                    value_col = c
                    break
        
        # 获取唯一的行列标签
        rows = df[row_col].unique().tolist()
        columns = df[col_col].unique().tolist()
        
        # 创建矩阵
        n_rows, n_cols = len(rows), len(columns)
        values = np.zeros((n_rows, n_cols))
        sizes = np.ones((n_rows, n_cols)) * 100  # 默认大小
        
        row_idx = {r: i for i, r in enumerate(rows)}
        col_idx = {c: i for i, c in enumerate(columns)}
        
        for _, r in df.iterrows():
            ri = row_idx[r[row_col]]
            ci = col_idx[r[col_col]]
            values[ri, ci] = r[value_col]
            if size_col and size_col in r:
                sizes[ri, ci] = r[size_col]
        
        return rows, columns, values, sizes
    
    else:
        # 矩阵格式：第一列为行标签
        rows = df.iloc[:, 0].astype(str).tolist()
        columns = cols[1:]
        values = df.iloc[:, 1:].values.astype(float)
        # 大小默认与值成比例
        sizes = (values - values.min()) / (values.max() - values.min()) * 100 + 75
        return rows, columns, values, sizes

rows, columns, values, sizes = parse_data(df)
print(f"矩阵大小: {len(rows)} x {len(columns)}")
print(f"值范围: {values.min():.1f} - {values.max():.1f}")
print(f"大小范围: {sizes.min():.1f} - {sizes.max():.1f}")

# ============================================================================
# 获取colormap
# ============================================================================
def get_cmap(colormap_name):
    """获取matplotlib colormap"""
    if colormap_name in COLOR_PALETTES:
        return COLOR_PALETTES[colormap_name]
    try:
        return plt.cm.get_cmap(colormap_name)
    except:
        return plt.cm.jet

cmap = get_cmap(config['colormap'])

# ============================================================================
# 绘制矩阵气泡图
# ============================================================================
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']), dpi=config['dpi'])

# 计算归一化值和大小
v_min, v_max = values.min(), values.max()
s_min, s_max = sizes.min(), sizes.max()

# 归一化颜色
norm = mcolors.Normalize(vmin=v_min, vmax=v_max)

# 大小缩放因子
size_scale = config['marker_size'] / 100 * 3  # 基础缩放

marker_style = config.get('marker_style', 'circle')
alpha = config.get('bubble_alpha', 0.9)

# 标记映射
MARKER_MAP = {
    'circle': 'o',
    'square': 's',
    'diamond': 'D',
    'triangle': '^'
}

# 绘制气泡
scatter = None
for i in range(len(rows)):
    for j in range(len(columns)):
        val = values[i, j]
        sz = sizes[i, j]
        
        # 归一化大小
        norm_size = (sz - s_min) / (s_max - s_min) if s_max > s_min else 0.5
        marker_s = (50 + norm_size * 150) * size_scale  # 散点大小
        
        marker = MARKER_MAP.get(marker_style, 'o')
        scatter = ax.scatter(j, i, s=marker_s, c=[val], cmap=cmap, 
                           vmin=v_min, vmax=v_max, alpha=alpha,
                           edgecolors='black', linewidth=0.5, marker=marker)
sm = scatter

# 添加颜色条
if config.get('show_colorbar', True):
    cbar = plt.colorbar(sm, ax=ax, shrink=0.7, pad=0.15)
    # 设置刻度
    ticks = np.linspace(v_min, v_max, 6)
    cbar.set_ticks(ticks)
    cbar.set_ticklabels([f'{t:.0f}' for t in ticks])

# 添加大小图例
if config.get('show_size_legend', True):
    # 在右上角添加大小图例
    legend_sizes = [75, 100, 125, 150]
    legend_y_start = 0.95
    legend_x = 1.12
    
    # 添加"Sizes"标题
    ax.text(legend_x, legend_y_start + 0.05, 'Sizes', transform=ax.transAxes,
           fontsize=11, fontweight='bold', ha='left')
    
    marker = MARKER_MAP.get(marker_style, 'o')
    for idx, sz in enumerate(legend_sizes):
        norm_size = (sz - s_min) / (s_max - s_min) if s_max > s_min else 0.5
        display_size = (50 + norm_size * 150) * size_scale * 0.5
        
        y_pos = legend_y_start - idx * 0.08
        ax.scatter([legend_x], [y_pos], s=display_size, c='gray', alpha=0.6,
                  transform=ax.transAxes, marker=marker,
                  edgecolors='none', clip_on=False)
        ax.text(legend_x + 0.08, y_pos, str(int(sz)), transform=ax.transAxes,
               fontsize=10, va='center', ha='left')

# 设置坐标轴
ax.set_xticks(range(len(columns)))
ax.set_xticklabels(columns, fontsize=10)
ax.set_yticks(range(len(rows)))
ax.set_yticklabels(rows, fontsize=10)

# 标签
if config['x_label']:
    ax.set_xlabel(config['x_label'], fontsize=12, fontweight='bold')
if config['y_label']:
    ax.set_ylabel(config['y_label'], fontsize=12, fontweight='bold')

# 标题
if config['title']:
    ax.set_title(config['title'], fontsize=14, fontweight='bold', pad=10)

# 网格线样式
line_style = config.get('line_style', 'solid')
if line_style != 'none' and config['show_grid']:
    line_map = {'solid': '-', 'dashed': '--', 'dotted': ':'}
    ax.set_axisbelow(True)
    ax.grid(True, linestyle=line_map.get(line_style, '-'), alpha=0.3, color='gray')

# 设置范围
ax.set_xlim(-0.5, len(columns) - 0.5)
ax.set_ylim(-0.5, len(rows) - 0.5)

# 设置边框
for spine in ax.spines.values():
    spine.set_visible(True)
    spine.set_linewidth(1)

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"图表已保存: output.png")
