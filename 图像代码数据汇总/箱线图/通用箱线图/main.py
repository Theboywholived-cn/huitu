# 通用箱线图模板
# 支持多组数据、颜色自定义、异常值显示等
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
    'jet': ['#E64B35', '#4DBBD5', '#00A087', '#F39B7F', '#8491B4', '#91D1C2'],
    'viridis': ['#440154', '#31688E', '#35B779', '#FDE725', '#26828E', '#1F9E89'],
    'plasma': ['#0D0887', '#7E03A8', '#CC4778', '#F89540', '#ED7953', '#FB9F3A'],
    'coolwarm': ['#3B4CC0', '#6788EE', '#9ABBFF', '#F7D4C9', '#F2A07B', '#B40426'],
    'RdYlBu': ['#D73027', '#F46D43', '#FDAE61', '#ABD9E9', '#74ADD1', '#4575B4'],
    'pastel': ['#E64B35', '#4DBBD5', '#00A087', '#F39B7F', '#8491B4', '#91D1C2'],
}

# ============================================================================
# 读取配置
# ============================================================================
def get_config():
    """获取图表配置"""
    default = {
        'colormap': 'jet',
        'colors': None,
        'title': '数据分布箱线图',
        'x_label': '分组',
        'y_label': '数值',
        'show_legend': False,
        'show_grid': True,
        'fig_width': 10,
        'fig_height': 8,
        'dpi': 150,
        # 箱线图专属配置
        'box_width': 0.6,            # 箱子宽度
        'box_alpha': 0.8,            # 箱子透明度
        'show_outliers': True,       # 显示异常值
        'show_notch': False,         # 显示缺口（置信区间）
        'show_means': False,         # 显示均值标记
        'median_color': 'white',     # 中位数线颜色
        'median_width': 2.0,         # 中位数线宽度
        'whisker_style': 'solid',    # 须线样式: solid, dashed
        'orient': 'vertical',        # 方向: vertical, horizontal
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
print(f"配置: colormap={config['colormap']}, box_width={config['box_width']}")

# ============================================================================
# 加载数据
# ============================================================================
def load_data():
    """智能查找并加载数据文件"""
    files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    files = [f for f in files if not f.startswith('_')]
    
    if not files:
        # 内置示例数据
        np.random.seed(42)
        return pd.DataFrame({
            '组别A': np.random.normal(50, 10, 100),
            '组别B': np.random.normal(55, 12, 100),
            '组别C': np.random.normal(48, 8, 100),
            '组别D': np.random.normal(60, 15, 100),
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
# 判断数据结构并准备箱线图数据
# ============================================================================
# 方式1: 每列是一个组（宽格式）
# 方式2: 有分组列和数值列（长格式）

numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
non_numeric_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]

# 检测数据格式
if len(non_numeric_cols) >= 1 and len(numeric_cols) >= 1:
    # 可能是长格式：第一个非数值列作为分组，第一个数值列作为数据
    group_col = non_numeric_cols[0]
    value_col = numeric_cols[0]
    groups = df[group_col].unique()
    
    # 如果分组数量合理（2-20），使用长格式
    if 2 <= len(groups) <= 20:
        print(f"检测到长格式数据: 分组列={group_col}, 数值列={value_col}")
        box_data = [df[df[group_col] == g][value_col].dropna().values for g in groups]
        labels = list(groups)
    else:
        # 使用宽格式
        print(f"使用宽格式数据: {len(numeric_cols)} 个数值列")
        box_data = [df[col].dropna().values for col in numeric_cols[:10]]
        labels = numeric_cols[:10]
else:
    # 宽格式：每个数值列是一个组
    print(f"使用宽格式数据: {len(numeric_cols)} 个数值列")
    box_data = [df[col].dropna().values for col in numeric_cols[:10]]
    labels = numeric_cols[:10]

n_groups = len(box_data)
print(f"共 {n_groups} 个组: {labels}")

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
    colors = get_colors(config['colormap'], n_groups)

# ============================================================================
# 绑图
# ============================================================================
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']), dpi=config['dpi'])

box_width = config.get('box_width', 0.6)
box_alpha = config.get('box_alpha', 0.8)
show_outliers = config.get('show_outliers', True)
show_notch = config.get('show_notch', False)
show_means = config.get('show_means', False)
median_color = config.get('median_color', 'white')
median_width = config.get('median_width', 2.0)
whisker_style = config.get('whisker_style', 'solid')
orient = config.get('orient', 'vertical')

# 须线样式映射
whisker_ls = {'solid': '-', 'dashed': '--', 'dotted': ':'}.get(whisker_style, '-')

# 异常值样式
flier_props = dict(
    marker='o',
    markerfacecolor='none',
    markeredgecolor='gray',
    markersize=6,
    alpha=0.7
) if show_outliers else dict(marker='')

# 均值样式
mean_props = dict(
    marker='D',
    markerfacecolor='white',
    markeredgecolor='black',
    markersize=6
)

# 绘制箱线图
if orient == 'horizontal':
    bp = ax.boxplot(box_data,
                    vert=False,
                    tick_labels=labels,
                    patch_artist=True,
                    widths=box_width,
                    notch=show_notch,
                    showmeans=show_means,
                    meanprops=mean_props,
                    showfliers=show_outliers,
                    flierprops=flier_props,
                    whiskerprops=dict(linestyle=whisker_ls, linewidth=1.2),
                    capprops=dict(linewidth=1.2))
else:
    bp = ax.boxplot(box_data,
                    vert=True,
                    tick_labels=labels,
                    patch_artist=True,
                    widths=box_width,
                    notch=show_notch,
                    showmeans=show_means,
                    meanprops=mean_props,
                    showfliers=show_outliers,
                    flierprops=flier_props,
                    whiskerprops=dict(linestyle=whisker_ls, linewidth=1.2),
                    capprops=dict(linewidth=1.2))

# 设置箱子颜色
for i, (patch, color) in enumerate(zip(bp['boxes'], colors)):
    patch.set_facecolor(color)
    patch.set_edgecolor('#333333')
    patch.set_linewidth(1.2)
    patch.set_alpha(box_alpha)
    
    # 中位数线
    bp['medians'][i].set_color(median_color)
    bp['medians'][i].set_linewidth(median_width)
    
    # 须线颜色
    if i * 2 < len(bp['whiskers']):
        bp['whiskers'][i * 2].set_color('#333333')
        bp['whiskers'][i * 2 + 1].set_color('#333333')
    
    # 端盖颜色
    if i * 2 < len(bp['caps']):
        bp['caps'][i * 2].set_color('#333333')
        bp['caps'][i * 2 + 1].set_color('#333333')

# ============================================================================
# 设置坐标轴和标签
# ============================================================================
x_label = config.get('x_label') or '分组'
y_label = config.get('y_label') or '数值'

if orient == 'horizontal':
    ax.set_xlabel(y_label, fontsize=12, fontweight='bold')
    ax.set_ylabel(x_label, fontsize=12, fontweight='bold')
else:
    ax.set_xlabel(x_label, fontsize=12, fontweight='bold')
    ax.set_ylabel(y_label, fontsize=12, fontweight='bold')

title = config.get('title') or '数据分布箱线图'
if title:
    ax.set_title(title, fontsize=14, fontweight='bold', pad=15)

# 网格
if config.get('show_grid', True):
    if orient == 'horizontal':
        ax.grid(True, linestyle='--', alpha=0.3, axis='x')
    else:
        ax.grid(True, linestyle='--', alpha=0.3, axis='y')
    ax.set_axisbelow(True)

# 调整刻度标签
ax.tick_params(axis='both', labelsize=11)

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"图表已保存: output.png")
