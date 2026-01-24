# 通用折线图模板 - 支持图表配置
import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# 预设配色方案
# ============================================================================
COLOR_PALETTES = {
    'Set1': ['#E41A1C', '#377EB8', '#4DAF4A', '#984EA3', '#FF7F00', '#FFFF33', '#A65628', '#F781BF'],
    'Set2': ['#66C2A5', '#FC8D62', '#8DA0CB', '#E78AC3', '#A6D854', '#FFD92F', '#E5C494', '#B3B3B3'],
    'Paired': ['#A6CEE3', '#1F78B4', '#B2DF8A', '#33A02C', '#FB9A99', '#E31A1C', '#FDBF6F', '#FF7F00'],
    'jet': ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4', '#91D1C2', '#DC0000'],
    'viridis': ['#440154', '#482878', '#3E4A89', '#31688E', '#26828E', '#1F9E89', '#35B779', '#6DCD59'],
    'plasma': ['#0D0887', '#46039F', '#7201A8', '#9C179E', '#BD3786', '#D8576B', '#ED7953', '#FB9F3A'],
    'coolwarm': ['#3B4CC0', '#6788EE', '#9ABBFF', '#C9D7F0', '#F7D4C9', '#F2A07B', '#D65244', '#B40426'],
    'RdYlBu': ['#D73027', '#F46D43', '#FDAE61', '#FEE090', '#E0F3F8', '#ABD9E9', '#74ADD1', '#4575B4'],
    'hot': ['#000000', '#8B0000', '#FF0000', '#FF4500', '#FFA500', '#FFFF00', '#FFFFFF'],
}

# ============================================================================
# 读取配置
# ============================================================================
# Marker 和 Line 样式映射
MARKER_MAP = {
    'circle': 'o', 'o': 'o',
    'square': 's', 's': 's',
    'diamond': 'D', 'D': 'D',
    'triangle': '^', '^': '^',
    'star': '*', '*': '*',
    'plus': '+', '+': '+',
    'x': 'x',
}

LINE_MAP = {
    'solid': '-', '-': '-',
    'dashed': '--', '--': '--',
    'dotted': ':', ':': ':',
    'dashdot': '-.', '-.': '-.',
}

def get_config():
    """获取图表配置"""
    default = {
        'x_column': None,
        'y_columns': None,
        'group_column': None,
        'marker_style': 'o',
        'marker_size': 8,
        'line_style': '-',
        'line_width': 2,
        'colors': None,
        'colormap': 'jet',
        'title': '',
        'x_label': '',
        'y_label': '',
        'show_legend': True,
        'show_grid': True,
        'fig_width': 10,
        'fig_height': 7,
        'dpi': 150
    }
    
    # 从 CHART_CONFIG 读取（优先级最高）
    try:
        cfg = CHART_CONFIG
        for k in default:
            val = getattr(cfg, k, None)
            if val is not None:
                default[k] = val
    except NameError:
        # 从 JSON 文件读取（备用）
        if os.path.exists('_chart_config.json'):
            try:
                with open('_chart_config.json', 'r', encoding='utf-8') as f:
                    cfg_json = json.load(f)
                    for k in default:
                        if k in cfg_json and cfg_json[k] is not None:
                            default[k] = cfg_json[k]
            except Exception:
                pass
    
    # 转换 marker 和 line 样式
    default['marker_style'] = MARKER_MAP.get(default['marker_style'], 'o')
    default['line_style'] = LINE_MAP.get(default['line_style'], '-')
    
    return default

config = get_config()
print(f"配置: colormap={config['colormap']}, marker={config['marker_style']}, line={config['line_style']}")

# ============================================================================
# 加载数据
# ============================================================================
def load_data():
    """智能查找并加载数据文件"""
    files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    files = [f for f in files if not f.startswith('_')]
    
    if not files:
        print("未找到数据文件，使用示例数据")
        np.random.seed(42)
        x = np.linspace(0, 10, 50)
        return pd.DataFrame({
            'X': x,
            'Y1': np.sin(x) + np.random.normal(0, 0.1, 50),
            'Y2': np.cos(x) + np.random.normal(0, 0.1, 50),
            'Y3': np.sin(x + 1) + np.random.normal(0, 0.1, 50),
        })
    
    # 选择第一个非示范数据文件
    target = files[0]
    for f in files:
        if "示范" not in f and "demo" not in f.lower():
            target = f
            break
    
    print(f"加载文件: {target}")
    
    if target.endswith('.csv'):
        for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
            try:
                return pd.read_csv(target, encoding=encoding)
            except:
                continue
        return pd.read_csv(target, encoding='utf-8', errors='replace')
    else:
        return pd.read_excel(target)

df = load_data()
print(f"数据: {len(df)} 行, {len(df.columns)} 列")
print(f"列名: {list(df.columns)}")

# ============================================================================
# 确定数据列
# ============================================================================
# X轴列
x_col = config['x_column']
if not x_col or x_col not in df.columns:
    # 优先选择非数值列（如日期、月份）
    non_numeric = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    if non_numeric:
        x_col = non_numeric[0]
    else:
        x_col = df.columns[0]

# Y轴列
y_cols = config['y_columns']
if not y_cols:
    # 自动选择所有数值列（排除X轴）
    y_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != x_col]
elif isinstance(y_cols, str):
    y_cols = [y_cols]

# 过滤有效列
y_cols = [c for c in y_cols if c in df.columns]

if not y_cols:
    raise ValueError(f"没有可用的Y轴数据列。数值列: {[c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]}")

print(f"使用列: X={x_col}, Y={y_cols}")

# ============================================================================
# 获取配色
# ============================================================================
def get_colors(colormap_name, count):
    """根据配色方案名称获取颜色列表"""
    if colormap_name in COLOR_PALETTES:
        palette = COLOR_PALETTES[colormap_name]
        # 循环使用颜色
        return [palette[i % len(palette)] for i in range(count)]
    else:
        # 使用 matplotlib colormap
        try:
            cmap = plt.cm.get_cmap(colormap_name)
            return [cmap(i / max(count - 1, 1)) for i in range(count)]
        except:
            return COLOR_PALETTES['jet'][:count]

# 使用配置的颜色或根据 colormap 生成
if config['colors']:
    colors = config['colors']
else:
    colors = get_colors(config['colormap'], len(y_cols))

print(f"配色方案: {config['colormap']}, 颜色数: {len(colors)}")

# ============================================================================
# 绑制图表
# ============================================================================
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']))

marker = config['marker_style']
marker_size = config['marker_size']
line_style = config['line_style']
line_width = config['line_width']

for i, y_col in enumerate(y_cols):
    color = colors[i] if i < len(colors) else colors[i % len(colors)]
    
    ax.plot(
        df[x_col], df[y_col],
        color=color,
        linestyle=line_style,
        linewidth=line_width,
        marker=marker,
        markersize=marker_size,
        markerfacecolor=color,
        markeredgecolor='white',
        markeredgewidth=0.5,
        alpha=0.9,
        label=y_col
    )

# 设置标签
ax.set_xlabel(config['x_label'] or x_col, fontsize=12, fontweight='bold')
ax.set_ylabel(config['y_label'] or '', fontsize=12, fontweight='bold')

# 设置标题
title = config['title'] or f"折线图"
ax.set_title(title, fontsize=14, fontweight='bold', pad=10)

# 图例
if config['show_legend'] and len(y_cols) > 1:
    ax.legend(loc='best', frameon=True, framealpha=0.95, fontsize=10)

# 网格
if config['show_grid']:
    ax.grid(True, linestyle='--', alpha=0.3, axis='both')
    ax.set_axisbelow(True)

# X轴标签旋转（如果标签太长）
if df[x_col].dtype == 'object':
    labels = df[x_col].astype(str)
    if labels.str.len().max() > 5:
        plt.xticks(rotation=45, ha='right')

# 美化
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"\n图表已保存: output.png")
