# 通用热力图模板 - 支持相关性热力图、矩阵热力图
import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# 配色方案映射
# ============================================================================
COLORMAP_OPTIONS = {
    'coolwarm': 'coolwarm',
    'RdYlBu': 'RdYlBu_r',
    'viridis': 'viridis',
    'plasma': 'plasma',
    'jet': 'jet',
    'hot': 'hot',
    'RdBu': 'RdBu_r',
    'seismic': 'seismic',
}

# ============================================================================
# 读取配置
# ============================================================================
def get_config():
    """获取图表配置"""
    default = {
        'colormap': 'coolwarm',
        'colors': None,
        'title': '',
        'x_label': '',
        'y_label': '',
        'show_legend': True,
        'show_grid': True,
        'fig_width': 10,
        'fig_height': 8,
        'dpi': 150,
        'y_columns': None,
        # 热力图专属配置
        'show_values': True,        # 显示数值
        'value_format': '.2f',      # 数值格式
        'show_colorbar': True,      # 显示颜色条
        'square_cells': True,       # 正方形单元格
        'heatmap_mode': 'correlation',  # 模式: correlation, matrix
        'center_zero': True,        # 颜色中心为0
        'line_width': 0.5,          # 单元格边框宽度
        'font_size': 10,            # 数值字体大小
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
print(f"配置: colormap={config['colormap']}, mode={config.get('heatmap_mode', 'correlation')}")

# ============================================================================
# 加载数据
# ============================================================================
def load_data():
    """智能查找并加载数据文件"""
    files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    files = [f for f in files if not f.startswith('_')]
    
    if not files:
        # 内置示例数据 - 有相关性的变量
        np.random.seed(42)
        n = 100
        var_a = np.random.randn(n)
        var_b = var_a * 0.8 + np.random.randn(n) * 0.3
        var_c = -var_a * 0.6 + np.random.randn(n) * 0.4
        var_d = np.random.randn(n)
        var_e = var_d * 0.7 + np.random.randn(n) * 0.5
        var_f = var_b * 0.5 + var_e * 0.3 + np.random.randn(n) * 0.3
        
        return pd.DataFrame({
            'Temperature': (var_a * 10 + 25).round(2),
            'Humidity': (var_b * 15 + 60).round(2),
            'Pressure': (var_c * 5 + 1013).round(2),
            'Wind_Speed': (np.abs(var_d) * 5 + 2).round(2),
            'Precipitation': (np.abs(var_e) * 10).round(2),
            'Visibility': (var_f * 3 + 10).round(2)
        })
    
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
# 选择数值列
# ============================================================================
y_cols = config.get('y_columns')
if not y_cols:
    y_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
else:
    y_cols = [c for c in y_cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]

if len(y_cols) < 2:
    y_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

print(f"数值列: {y_cols}")

# ============================================================================
# 准备热力图数据
# ============================================================================
heatmap_mode = config.get('heatmap_mode', 'correlation')

if heatmap_mode == 'correlation':
    # 计算相关性矩阵
    matrix_data = df[y_cols].corr()
    default_title = '变量相关性热力图'
    vmin, vmax = -1, 1
    center = 0 if config.get('center_zero', True) else None
else:
    # 直接使用数据作为矩阵（假设数据已经是矩阵形式）
    matrix_data = df[y_cols]
    default_title = '热力图'
    vmin, vmax = None, None
    center = 0 if config.get('center_zero', True) else None

# ============================================================================
# 绑图
# ============================================================================
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']), dpi=config['dpi'])

# 获取配色
cmap_name = config.get('colormap', 'coolwarm')
cmap = COLORMAP_OPTIONS.get(cmap_name, cmap_name)

# 数值格式
fmt = config.get('value_format', '.2f')

# 绑制热力图
heatmap_kwargs = {
    'data': matrix_data,
    'annot': config.get('show_values', True),
    'fmt': fmt,
    'cmap': cmap,
    'square': config.get('square_cells', True),
    'linewidths': config.get('line_width', 0.5),
    'linecolor': 'white',
    'cbar': config.get('show_colorbar', True),
    'ax': ax,
    'annot_kws': {'size': config.get('font_size', 10)},
}

# 相关性热力图特殊设置
if heatmap_mode == 'correlation':
    heatmap_kwargs['center'] = center
    heatmap_kwargs['vmin'] = vmin
    heatmap_kwargs['vmax'] = vmax
    heatmap_kwargs['cbar_kws'] = {'shrink': 0.8}
elif center is not None:
    heatmap_kwargs['center'] = center

sns.heatmap(**heatmap_kwargs)

# ============================================================================
# 设置标签和标题
# ============================================================================
title = config.get('title') or default_title
ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

if config.get('x_label'):
    ax.set_xlabel(config['x_label'], fontsize=12)
if config.get('y_label'):
    ax.set_ylabel(config['y_label'], fontsize=12)

# 旋转X轴标签
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"图表已保存: output.png")
