# 百分比堆积柱形图绘制示例
# 支持 ChartConfig 配置和配色方案选择
import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import ticker
import matplotlib as mpl

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# 预设配色方案
# ============================================================================
COLOR_PALETTES = {
    'jet': ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4', '#91D1C2', '#DC0000'],
    'viridis': ['#440154', '#482878', '#3E4A89', '#31688E', '#26828E', '#1F9E89', '#35B779', '#6DCD59'],
    'plasma': ['#0D0887', '#46039F', '#7201A8', '#9C179E', '#BD3786', '#D8576B', '#ED7953', '#FB9F3A'],
    'coolwarm': ['#3B4CC0', '#6788EE', '#9ABBFF', '#C9D7F0', '#F7D4C9', '#F2A07B', '#D65244', '#B40426'],
    'RdYlBu': ['#D73027', '#F46D43', '#FDAE61', '#FEE090', '#E0F3F8', '#ABD9E9', '#74ADD1', '#4575B4'],
    'hot': ['#8B0000', '#CD0000', '#FF0000', '#FF4500', '#FFA500', '#FFD700', '#FFFF00', '#FFFFFF'],
    'NEJM': ['#BC3C29', '#0072B5', '#E18727', '#20854E', '#7876B1', '#6F99AD', '#FFDC91', '#EE4C97'],
    'Set1': ['#E41A1C', '#377EB8', '#4DAF4A', '#984EA3', '#FF7F00', '#FFFF33', '#A65628', '#F781BF'],
    'Set2': ['#66C2A5', '#FC8D62', '#8DA0CB', '#E78AC3', '#A6D854', '#FFD92F', '#E5C494', '#B3B3B3'],
    'Paired': ['#A6CEE3', '#1F78B4', '#B2DF8A', '#33A02C', '#FB9A99', '#E31A1C', '#FDBF6F', '#FF7F00'],
}

# ============================================================================
# 读取配置
# ============================================================================
def get_config():
    """获取图表配置"""
    default = {
        'colormap': 'jet',
        'colors': None,
        'title': '百分比堆积柱形图',
        'x_label': '',
        'y_label': '百分比',
        'show_legend': True,
        'show_grid': False,
        'fig_width': 10,
        'fig_height': 6,
        'dpi': 150,
        # 柱形图专属配置
        'bar_width': 0.6,
        'show_values': True,  # 显示数值标签
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
print(f"配置: colormap={config['colormap']}, bar_width={config.get('bar_width', 0.6)}")

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
            '类别': ['one', 'two', 'three', 'four', 'five'],
            'type01': [10, 8, 5, 10, 2],
            'type02': [13, 10, 7, 4, 10],
            'type03': [5, 7, 10, 6, 8],
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
# 找分类列和数值列
category_col = None
value_cols = []

for col in df.columns:
    if pd.api.types.is_numeric_dtype(df[col]):
        value_cols.append(col)
    elif category_col is None:
        category_col = col

# 如果没有分类列，用索引
if category_col is None:
    df['_index'] = [f'类别{i+1}' for i in range(len(df))]
    category_col = '_index'

# 至少需要一个数值列
if not value_cols:
    print("警告: 没有找到数值列，使用示例数据")
    df = pd.DataFrame({
        '类别': ['A', 'B', 'C', 'D', 'E'],
        '系列1': [10, 8, 5, 10, 2],
        '系列2': [13, 10, 7, 4, 10],
        '系列3': [5, 7, 10, 6, 8],
    })
    category_col = '类别'
    value_cols = ['系列1', '系列2', '系列3']

print(f"分类列: {category_col}, 数值列: {value_cols}")

# ============================================================================
# 获取配色
# ============================================================================
def get_colors(colormap_name, count):
    """根据配色方案获取颜色列表"""
    if colormap_name in COLOR_PALETTES:
        palette = COLOR_PALETTES[colormap_name]
        return [palette[i % len(palette)] for i in range(count)]
    else:
        # 尝试使用 matplotlib colormap
        try:
            cmap = plt.cm.get_cmap(colormap_name)
            return [cmap(i / max(count - 1, 1)) for i in range(count)]
        except:
            return COLOR_PALETTES['jet'][:count]

# 获取颜色
if config['colors'] and len(config['colors']) > 0:
    colors = config['colors']
else:
    colors = get_colors(config['colormap'], len(value_cols))

print(f"配色方案: {config['colormap']}, 颜色数: {len(colors)}")

# ============================================================================
# 绑制百分比堆积柱形图
# ============================================================================
labels = df[category_col].astype(str).tolist()
data_list = [df[col].values for col in value_cols]

# 计算百分比
all_data = np.array(data_list)
sums = np.sum(all_data, axis=0)
sums[sums == 0] = 1  # 避免除零

# 创建图形
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']), dpi=config['dpi'])

# 绘制堆积柱形图
bottom_y = np.zeros(len(labels))
bar_width = config.get('bar_width', 0.6)

for i, (data, label) in enumerate(zip(all_data, value_cols)):
    y = data / sums  # 百分比
    color = colors[i % len(colors)]
    ax.bar(labels, y, bar_width, bottom=bottom_y, color=color, label=label, ec='white', linewidth=0.5)
    bottom_y = y + bottom_y

# 设置样式
ax.tick_params(which='major', direction='in', length=3, width=1., bottom=False)
for spine in ["top", "left", "right"]:
    ax.spines[spine].set_visible(False)
ax.spines['bottom'].set_linewidth(1.5)

# 设置刻度
locator = ticker.FixedLocator(range(len(labels)))
ax.xaxis.set_major_locator(locator)
ax.set_xticklabels(labels, fontsize=11, rotation=45 if len(labels) > 6 else 0, 
                   ha='right' if len(labels) > 6 else 'center')

ax.set_ylim(ymin=0, ymax=1.05)
ax.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1))

# 添加数值标签
if config.get('show_values', True):
    for c in ax.containers:
        # 根据背景色决定文字颜色
        ax.bar_label(c, label_type='center', fontsize=10,
                     labels=[f'{v*100:.1f}' if v > 0.05 else '' for v in c.datavalues],
                     color='white', fontweight='bold')

# 图例
if config['show_legend']:
    ax.legend(ncol=min(len(value_cols), 4), frameon=False, loc="upper center", 
              bbox_to_anchor=(0.5, 1.12), fontsize=10)

# 网格
if config['show_grid']:
    ax.grid(True, axis='y', linestyle='--', alpha=0.3)

# 标签
if config['x_label']:
    ax.set_xlabel(config['x_label'], fontsize=12)
if config['y_label']:
    ax.set_ylabel(config['y_label'], fontsize=12)

# 标题
title = config['title'] or '百分比堆积柱形图'
ax.set_title(title, fontsize=14, fontweight='bold', pad=25)

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"图表已保存: output.png")
