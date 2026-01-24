# 通用柱状图模板
# 支持分组柱状图、配色方案、柱宽和透明度调节
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
    'jet': ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4'],
    'viridis': ['#440154', '#31688E', '#35B779', '#FDE725', '#26828E', '#1F9E89'],
    'plasma': ['#0D0887', '#7E03A8', '#CC4778', '#F89540', '#ED7953', '#FB9F3A'],
    'coolwarm': ['#3B4CC0', '#6788EE', '#9ABBFF', '#F7D4C9', '#F2A07B', '#B40426'],
    'RdYlBu': ['#D73027', '#F46D43', '#FDAE61', '#ABD9E9', '#74ADD1', '#4575B4'],
    'hot': ['#8B0000', '#FF0000', '#FF4500', '#FFA500', '#FFFF00', '#FFFFFF'],
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
        'x_column': None,
        'y_columns': None,
        'show_legend': True,
        'show_grid': True,
        'fig_width': 10,
        'fig_height': 8,
        'dpi': 150,
        # 柱状图专属配置
        'bar_width': 0.8,           # 柱子宽度
        'bubble_alpha': 0.85,       # 透明度
        'show_values': False,       # 显示数值标签
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
print(f"配置: colormap={config['colormap']}, bar_width={config['bar_width']}")

# ============================================================================
# 加载数据
# ============================================================================
def load_data():
    """智能查找并加载数据文件"""
    files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    files = [f for f in files if not f.startswith('_')]
    
    if not files:
        # 内置示例数据
        return pd.DataFrame({
            '类别': ['A', 'B', 'C', 'D', 'E'],
            '数值1': [23, 45, 32, 67, 54],
            '数值2': [31, 38, 42, 59, 48],
            '数值3': [28, 51, 35, 62, 43],
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
# 确定数据列
# ============================================================================
x_col = config['x_column']
if not x_col or x_col not in df.columns:
    # 选择第一个非数值列或第一列作为X轴
    non_numeric = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    x_col = non_numeric[0] if non_numeric else df.columns[0]

y_cols = config['y_columns']
if not y_cols:
    # 选择所有数值列作为Y轴
    y_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != x_col][:6]
y_cols = [c for c in y_cols if c in df.columns]

print(f"X轴: {x_col}, Y轴: {y_cols}")

# ============================================================================
# 获取配色
# ============================================================================
def get_colors(colormap_name, count):
    """根据配色方案获取颜色列表"""
    if colormap_name in COLOR_PALETTES:
        palette = COLOR_PALETTES[colormap_name]
        return [palette[i % len(palette)] for i in range(count)]
    else:
        try:
            cmap = plt.cm.get_cmap(colormap_name)
            return [cmap(i / max(count - 1, 1)) for i in range(count)]
        except:
            return COLOR_PALETTES['jet'][:count]

if config['colors'] and len(config['colors']) > 0:
    colors = config['colors']
else:
    colors = get_colors(config['colormap'], len(y_cols))

# ============================================================================
# 绑制柱状图
# ============================================================================
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']), dpi=config['dpi'])

x = np.arange(len(df[x_col]))
n_bars = len(y_cols)
bar_width = config['bar_width']
alpha = config.get('bubble_alpha', 0.85)

# 计算每个柱子的偏移
if n_bars > 1:
    total_width = bar_width
    single_width = total_width / n_bars
    offsets = np.linspace(-total_width/2 + single_width/2, total_width/2 - single_width/2, n_bars)
else:
    single_width = bar_width
    offsets = [0]

# 绑制每个系列
bars_list = []
for i, y_col in enumerate(y_cols):
    color = colors[i % len(colors)]
    bars = ax.bar(x + offsets[i], df[y_col], width=single_width * 0.9, 
                  color=color, label=y_col, alpha=alpha, edgecolor='white', linewidth=0.5)
    bars_list.append(bars)
    
    # 显示数值标签
    if config.get('show_values', False):
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f'{height:.0f}',
                       xy=(bar.get_x() + bar.get_width() / 2, height),
                       xytext=(0, 3),
                       textcoords="offset points",
                       ha='center', va='bottom', fontsize=8)

# 设置X轴
ax.set_xticks(x)
ax.set_xticklabels(df[x_col], rotation=45 if len(df) > 6 else 0, 
                   ha='right' if len(df) > 6 else 'center')

# 标签
ax.set_xlabel(config['x_label'] or x_col, fontsize=12, fontweight='bold')
ax.set_ylabel(config['y_label'] or ', '.join(y_cols), fontsize=12, fontweight='bold')

# 标题
title = config['title'] or f"柱状图: {', '.join(y_cols)}"
ax.set_title(title, fontsize=14, fontweight='bold', pad=10)

# 图例
if config['show_legend'] and n_bars > 1:
    ax.legend(loc='best', frameon=True, fancybox=True)

# 网格
if config['show_grid']:
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"图表已保存: output.png")
