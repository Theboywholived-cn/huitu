# 小提琴图绘制示例
# 完整的小提琴图（带箱线图和散点）
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
# 预设配色方案
# ============================================================================
COLOR_PALETTES = {
    'Set1': ['#E41A1C', '#377EB8', '#4DAF4A', '#984EA3', '#FF7F00', '#FFFF33'],
    'Set2': ['#66C2A5', '#FC8D62', '#8DA0CB', '#E78AC3', '#A6D854', '#FFD92F'],
    'Paired': ['#A6CEE3', '#1F78B4', '#B2DF8A', '#33A02C', '#FB9A99', '#E31A1C'],
    'jet': ['#00A087', '#4DBBD5', '#E64B35', '#3C5488', '#F39B7F', '#8491B4'],
    'viridis': ['#440154', '#31688E', '#35B779', '#FDE725'],
    'plasma': ['#0D0887', '#7E03A8', '#CC4778', '#F89540'],
    'pastel': ['#66C2A5', '#4DBBD5', '#E78AC3'],  # 参考图片配色
    'coolwarm': ['#3B4CC0', '#7695F3', '#F2A07B', '#B40426'],
    'RdYlBu': ['#D73027', '#FC8D59', '#FEE090', '#91BFDB', '#4575B4'],
    'hot': ['#E60000', '#FFA500', '#FFFF00'],
}

# ============================================================================
# 读取配置
# ============================================================================
def get_config():
    """获取图表配置"""
    default = {
        'x_column': None,        # 分组列
        'y_columns': None,       # 数值列
        'colormap': 'pastel',
        'colors': None,
        'title': '',
        'x_label': '',
        'y_label': '',
        'show_legend': False,
        'show_grid': False,
        'fig_width': 8,
        'fig_height': 6,
        'dpi': 150,
        # 小提琴图专属配置
        'violin_style': 1,        # 样式 1-4
        'show_box': True,         # 显示箱线图
        'show_points': True,      # 显示散点
        'point_size': 5,          # 散点大小
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
print(f"配置: colormap={config['colormap']}, show_box={config.get('show_box', True)}, show_points={config.get('show_points', True)}")

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
        n = 100
        data = {
            'Class': ['cluster1'] * n + ['cluster2'] * n + ['cluster3'] * n,
            'Values': np.concatenate([
                np.random.normal(40, 5, n),
                np.random.normal(48, 5, n),
                np.random.normal(50, 4, n)
            ])
        }
        return pd.DataFrame(data)
    
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
# 分组列 (X轴)
x_col = config['x_column']
if not x_col or x_col not in df.columns:
    for col in df.columns:
        if '组' in col or 'group' in col.lower() or 'class' in col.lower() or 'cluster' in col.lower():
            x_col = col
            break
    if not x_col:
        non_numeric = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
        x_col = non_numeric[0] if non_numeric else df.columns[0]

# 数值列 (Y轴)
y_col = config['y_columns']
if isinstance(y_col, list):
    y_col = y_col[0] if y_col else None
if not y_col or y_col not in df.columns:
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    y_col = numeric_cols[0] if numeric_cols else df.columns[1]

print(f"使用列: X={x_col}, Y={y_col}")

# ============================================================================
# 获取配色
# ============================================================================
def get_colors(colormap_name, count):
    if colormap_name in COLOR_PALETTES:
        palette = COLOR_PALETTES[colormap_name]
        return [palette[i % len(palette)] for i in range(count)]
    else:
        try:
            return sns.color_palette(colormap_name, count)
        except:
            return COLOR_PALETTES['pastel'][:count]

groups = df[x_col].unique()
n_groups = len(groups)

if config['colors'] and len(config['colors']) > 0:
    colors = config['colors']
else:
    colors = get_colors(config['colormap'], n_groups)
    
print(f"分组数: {n_groups}, 配色方案: {config['colormap']}")

# ============================================================================
# 绑制小提琴图
# ============================================================================
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']))

# 获取配置
show_box = config.get('show_box', True)
show_points = config.get('show_points', True)
point_size = config.get('point_size', 5)

# 确定 inner 参数
if show_box:
    inner = 'box'
else:
    inner = None

# 绑制小提琴图
violin_parts = sns.violinplot(
    data=df, 
    x=x_col, 
    y=y_col, 
    hue=x_col,
    palette=colors,
    ax=ax,
    inner=inner,
    linewidth=1,
    saturation=0.8,
    legend=False,
)

# 添加散点
if show_points:
    sns.stripplot(
        data=df,
        x=x_col,
        y=y_col,
        color='#555555',
        alpha=0.6,
        size=point_size,
        ax=ax,
        jitter=0.15,
        edgecolor='white',
        linewidth=0.5,
    )

# 设置标签
ax.set_xlabel(config['x_label'] or x_col, fontsize=12, fontweight='bold')
ax.set_ylabel(config['y_label'] or y_col, fontsize=12, fontweight='bold')

# 标题
if config['title']:
    ax.set_title(config['title'], fontsize=14, fontweight='bold', pad=10)

# 网格
if config['show_grid']:
    ax.grid(True, linestyle='--', alpha=0.3, axis='y')
    ax.set_axisbelow(True)

# 美化
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"\n图表已保存: output.png")
