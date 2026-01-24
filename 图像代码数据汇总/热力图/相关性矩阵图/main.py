# 相关性矩阵图绘制示例
# 支持多种样式：气泡图（圆形/方形）、热力图、数值标注、三角矩阵
import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import PatchCollection
import matplotlib.colors as mcolors

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# 读取配置
# ============================================================================
def get_config():
    """获取图表配置"""
    default = {
        'colormap': 'RdBu_r',
        'colors': None,
        'title': '',
        'x_label': '',
        'y_label': '',
        'show_legend': True,
        'show_grid': True,
        'fig_width': 10,
        'fig_height': 10,
        'dpi': 150,
        # 相关性矩阵专属配置
        'matrix_style': 'circle',     # 样式: circle, square, heatmap, values
        'display_mode': 'full',       # 显示模式: full, lower, upper
        'show_values': False,         # 显示数值
        'value_format': '.2f',        # 数值格式
        'font_size': 10,              # 数值字体大小
        'show_colorbar': True,        # 显示颜色条
        'grid_color': '#888888',      # 网格颜色
        'grid_width': 1.5,            # 网格线宽
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
print(f"配置: matrix_style={config['matrix_style']}, display_mode={config['display_mode']}")

# ============================================================================
# 加载数据
# ============================================================================
def load_data():
    """智能查找并加载数据文件"""
    files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    files = [f for f in files if not f.startswith('_')]
    
    if not files:
        # 内置示例数据 - 生成相关性矩阵
        np.random.seed(42)
        n_vars = 11
        labels = list('fbdejahikcg')
        
        # 生成模拟相关性矩阵
        data = np.random.randn(100, n_vars)
        # 添加一些相关性
        data[:, 1] = data[:, 0] * 0.7 + np.random.randn(100) * 0.3
        data[:, 2] = data[:, 0] * 0.6 + np.random.randn(100) * 0.4
        data[:, 6] = data[:, 5] * 0.8 + np.random.randn(100) * 0.2
        data[:, 7] = data[:, 5] * 0.7 + np.random.randn(100) * 0.3
        
        df = pd.DataFrame(data, columns=labels)
        return df
    
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
# 计算相关性矩阵
# ============================================================================
# 只选择数值列
numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
if len(numeric_cols) < 2:
    raise ValueError("数据中需要至少2个数值列来计算相关性")

df_numeric = df[numeric_cols]
corr_matrix = df_numeric.corr()
labels = list(corr_matrix.columns)
n = len(labels)

print(f"相关性矩阵: {n}x{n}")

# ============================================================================
# 绑图
# ============================================================================
matrix_style = config.get('matrix_style', 'circle')
display_mode = config.get('display_mode', 'full')
show_values = config.get('show_values', False)
value_format = config.get('value_format', '.2f')
font_size = config.get('font_size', 10)
show_colorbar = config.get('show_colorbar', True)
grid_color = config.get('grid_color', '#888888')
grid_width = config.get('grid_width', 1.5)

fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']), dpi=config['dpi'])

# 创建颜色映射（蓝-白-红）
cmap = plt.colormaps.get_cmap('RdBu_r')
norm = mcolors.Normalize(vmin=-1, vmax=1)

# 获取相关性值
corr_values = corr_matrix.values

# ============================================================================
# 根据样式绑制
# ============================================================================
if matrix_style in ['circle', 'square']:
    # 气泡图样式（圆形或方形）
    patches = []
    colors_list = []
    
    for i in range(n):
        for j in range(n):
            # 根据显示模式决定是否绘制
            if display_mode == 'lower' and j > i:
                continue
            elif display_mode == 'upper' and j < i:
                continue
            
            val = corr_values[i, j]
            # 气泡大小与相关系数绝对值成正比
            size = abs(val) * 0.45  # 最大半径为0.45（留出边距）
            
            if size < 0.02:  # 太小就不画了
                continue
            
            x, y = j + 0.5, n - i - 0.5
            
            if matrix_style == 'circle':
                patch = mpatches.Circle((x, y), size, linewidth=0)
            else:  # square
                # 方形，边长 = size * 2
                half = size
                patch = mpatches.Rectangle((x - half, y - half), half * 2, half * 2, linewidth=0)
            
            patches.append(patch)
            colors_list.append(cmap(norm(val)))
    
    collection = PatchCollection(patches, facecolors=colors_list, edgecolors='none')
    ax.add_collection(collection)
    
    # 绘制网格
    for i in range(n + 1):
        ax.axhline(i, color=grid_color, linewidth=grid_width, zorder=1)
        ax.axvline(i, color=grid_color, linewidth=grid_width, zorder=1)

elif matrix_style == 'heatmap':
    # 热力图样式
    # 根据显示模式处理矩阵
    plot_matrix = corr_values.copy()
    if display_mode == 'lower':
        mask = np.triu_indices(n, k=1)
        plot_matrix[mask] = np.nan
    elif display_mode == 'upper':
        mask = np.tril_indices(n, k=-1)
        plot_matrix[mask] = np.nan
    
    im = ax.imshow(plot_matrix, cmap='RdBu_r', vmin=-1, vmax=1, aspect='equal')
    
    # 绘制网格
    for i in range(n + 1):
        ax.axhline(i - 0.5, color=grid_color, linewidth=grid_width)
        ax.axvline(i - 0.5, color=grid_color, linewidth=grid_width)

elif matrix_style == 'values':
    # 纯数值显示样式
    for i in range(n):
        for j in range(n):
            # 根据显示模式决定是否绘制
            if display_mode == 'lower' and j > i:
                continue
            elif display_mode == 'upper' and j < i:
                continue
            
            val = corr_values[i, j]
            color = cmap(norm(val))
            
            # 使用更小的字体显示数值
            text_color = color
            ax.text(j + 0.5, n - i - 0.5, f'{val:{value_format}}', 
                   ha='center', va='center', fontsize=font_size,
                   color=text_color, fontweight='bold')
    
    # 绘制网格
    for i in range(n + 1):
        ax.axhline(i, color=grid_color, linewidth=grid_width)
        ax.axvline(i, color=grid_color, linewidth=grid_width)

# ============================================================================
# 添加数值标注（对于气泡图样式）
# ============================================================================
if show_values and matrix_style in ['circle', 'square']:
    for i in range(n):
        for j in range(n):
            if display_mode == 'lower' and j > i:
                continue
            elif display_mode == 'upper' and j < i:
                continue
            
            val = corr_values[i, j]
            if abs(val) > 0.02:
                x, y = j + 0.5, n - i - 0.5
                # 根据背景亮度选择文字颜色
                text_color = 'white' if abs(val) > 0.5 else 'black'
                ax.text(x, y, f'{val:{value_format}}', ha='center', va='center',
                       fontsize=font_size - 2, color=text_color, fontweight='bold')

# ============================================================================
# 设置坐标轴
# ============================================================================
if matrix_style == 'heatmap':
    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_yticklabels(labels, fontsize=12)
else:
    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_xticks(np.arange(n) + 0.5)
    ax.set_yticks(np.arange(n) + 0.5)
    ax.set_xticklabels(labels, fontsize=12)
    ax.set_yticklabels(labels[::-1], fontsize=12)

# 将 x 轴标签放在顶部
ax.xaxis.set_ticks_position('top')
ax.xaxis.set_label_position('top')

# 移除边框
for spine in ax.spines.values():
    spine.set_visible(False)

ax.tick_params(axis='both', which='both', length=0)

# ============================================================================
# 添加颜色条
# ============================================================================
if show_colorbar:
    sm = plt.cm.ScalarMappable(cmap='RdBu_r', norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.8, aspect=30, pad=0.02)
    cbar.ax.tick_params(labelsize=10)

# 标题
title = config.get('title')
if title:
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

ax.set_aspect('equal')
plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"图表已保存: output.png")
