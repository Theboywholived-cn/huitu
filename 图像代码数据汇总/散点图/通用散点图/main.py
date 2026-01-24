# 通用散点图模板 - 支持图表配置
# 此模板能够读取 ChartConfig 配置来自定义图表样式
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# 读取配置 - 兼容无配置和有配置两种模式
# ============================================================================
def get_config():
    """获取图表配置，优先使用注入的 CHART_CONFIG，否则用默认值"""
    default = {
        'x_column': None,
        'y_columns': None,
        'group_column': None,
        'marker_style': 'o',
        'marker_size': 8,
        'line_style': '-',
        'line_width': 1.5,
        'colors': ['#E64B35', '#4DBBD5', '#00A087', '#F39B7F', '#8491B4', '#91D1C2'],
        'colormap': 'viridis',
        'title': '',
        'x_label': '',
        'y_label': '',
        'show_legend': True,
        'show_grid': True,
        'fig_width': 10,
        'fig_height': 8,
        'dpi': 150
    }
    
    # 尝试从注入的 CHART_CONFIG 读取（由后端在代码开头注入）
    try:
        cfg = CHART_CONFIG
        return {
            'x_column': getattr(cfg, 'x_column', default['x_column']),
            'y_columns': getattr(cfg, 'y_columns', default['y_columns']),
            'group_column': getattr(cfg, 'group_column', default['group_column']),
            'marker_style': getattr(cfg, 'marker_style', default['marker_style']),
            'marker_size': getattr(cfg, 'marker_size', default['marker_size']),
            'line_style': getattr(cfg, 'line_style', default['line_style']),
            'line_width': getattr(cfg, 'line_width', default['line_width']),
            'colors': getattr(cfg, 'colors', default['colors']),
            'colormap': getattr(cfg, 'colormap', default['colormap']),
            'title': getattr(cfg, 'title', default['title']),
            'x_label': getattr(cfg, 'x_label', default['x_label']),
            'y_label': getattr(cfg, 'y_label', default['y_label']),
            'show_legend': getattr(cfg, 'show_legend', default['show_legend']),
            'show_grid': getattr(cfg, 'show_grid', default['show_grid']),
            'fig_width': getattr(cfg, 'fig_width', default['fig_width']),
            'fig_height': getattr(cfg, 'fig_height', default['fig_height']),
            'dpi': getattr(cfg, 'dpi', default['dpi']),
        }
    except NameError:
        pass
    
    # 尝试从 JSON 文件读取
    if os.path.exists('_chart_config.json'):
        try:
            with open('_chart_config.json', 'r', encoding='utf-8') as f:
                cfg_json = json.load(f)
                default.update(cfg_json)
        except Exception:
            pass
    
    return default

config = get_config()

# ============================================================================
# 数据加载
# ============================================================================
def load_data():
    """加载数据文件"""
    for fname in os.listdir('.'):
        ext = fname.split('.')[-1].lower()
        if ext == 'csv':
            try:
                for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                    try:
                        return pd.read_csv(fname, encoding=encoding)
                    except UnicodeDecodeError:
                        continue
            except Exception:
                continue
        elif ext in ['xlsx', 'xls']:
            try:
                return pd.read_excel(fname)
            except Exception:
                continue
    
    # 生成示例数据
    np.random.seed(42)
    n = 100
    return pd.DataFrame({
        'X': np.linspace(0, 100, n),
        'Y1': np.linspace(0, 100, n) + np.random.normal(0, 5, n),
        'Y2': np.linspace(0, 100, n) + np.random.normal(3, 8, n),
        'Y3': np.linspace(0, 100, n) + np.random.normal(-2, 6, n),
    })

df = load_data()

# ============================================================================
# 绑定数据列
# ============================================================================
# X 列
x_col = config['x_column']
if x_col and x_col in df.columns:
    x_data = df[x_col]
else:
    # 使用第一列或索引
    x_data = df.iloc[:, 0] if len(df.columns) > 0 else pd.Series(range(len(df)))
    x_col = df.columns[0] if len(df.columns) > 0 else 'Index'

# Y 列
y_cols = config['y_columns']
if not y_cols:
    # 自动选择数值列
    y_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != x_col][:4]

# 过滤存在的列
y_cols = [c for c in y_cols if c in df.columns]
if not y_cols:
    # Fallback
    y_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])][:1]

# ============================================================================
# 绑定配置
# ============================================================================
# 配色方案
COLOR_PALETTES = {
    'jet': ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4'],
    'viridis': ['#440154', '#31688E', '#35B779', '#FDE725', '#26828E', '#1F9E89'],
    'plasma': ['#0D0887', '#7E03A8', '#CC4778', '#F89540', '#ED7953', '#FB9F3A'],
    'coolwarm': ['#3B4CC0', '#6788EE', '#9ABBFF', '#F7D4C9', '#F2A07B', '#B40426'],
    'RdYlBu': ['#D73027', '#F46D43', '#FDAE61', '#ABD9E9', '#74ADD1', '#4575B4'],
    'hot': ['#8B0000', '#FF0000', '#FF4500', '#FFA500', '#FFFF00', '#FFFFFF'],
}

if config['colors'] and len(config['colors']) > 0:
    colors = config['colors']
else:
    colors = COLOR_PALETTES.get(config['colormap'], COLOR_PALETTES['jet'])

marker = config['marker_style']
marker_size = config['marker_size']
line_style = config['line_style']
line_width = config['line_width']

# ============================================================================
# 绑定
# ============================================================================
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']), dpi=config['dpi'])

for i, y_col in enumerate(y_cols):
    color = colors[i % len(colors)]
    y_data = df[y_col]
    
    # 绘制散点
    ax.scatter(x_data, y_data, 
               c=color, 
               marker=marker, 
               s=marker_size ** 2,
               alpha=0.7, 
               edgecolors='white', 
               linewidth=0.5,
               label=y_col)
    
    # 可选：绘制趋势线
    if line_width > 0:
        z = np.polyfit(x_data.values, y_data.values, 1)
        p = np.poly1d(z)
        ax.plot(sorted(x_data), p(sorted(x_data)), 
                color=color, 
                linestyle=line_style, 
                linewidth=line_width, 
                alpha=0.8)

# 标签
ax.set_xlabel(config['x_label'] or x_col, fontsize=12)
ax.set_ylabel(config['y_label'] or ', '.join(y_cols), fontsize=12)

# 标题
title = config['title'] or f"数据可视化: {', '.join(y_cols)} vs {x_col}"
ax.set_title(title, fontsize=14, fontweight='bold')

# 图例
if config['show_legend'] and len(y_cols) > 1:
    ax.legend(loc='best', frameon=True, framealpha=0.9)

# 网格
if config['show_grid']:
    ax.grid(True, linestyle='--', alpha=0.3)

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"图表已保存: output.png")
print(f"X 轴: {x_col}")
print(f"Y 轴: {y_cols}")
