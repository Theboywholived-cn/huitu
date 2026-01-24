# 分组误差柱形图
# 根据上传的数据生成分组误差柱形图（带数据点）
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
# 读取配置
# ============================================================================
def get_config():
    default = {
        'x_column': None,       # X轴分组列
        'y_columns': None,      # Y轴数值列
        'group_column': None,   # 分组/hue列
        'colormap': 'Set1',
        'colors': None,
        'title': '分组误差柱形图',
        'x_label': '',
        'y_label': '',
        'show_points': True,    # 是否显示数据点
        'show_error': True,     # 是否显示误差线
        'error_type': 'sd',     # 误差类型: sd, se, ci
        'bar_width': 0.8,
        'point_size': 5,
        'fig_width': 10,
        'fig_height': 7,
        'dpi': 150
    }
    
    try:
        cfg = CHART_CONFIG
        for k in default:
            val = getattr(cfg, k, None)
            if val is not None:
                default[k] = val
    except NameError:
        pass
    
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
print(f"配置: colormap={config['colormap']}, show_points={config.get('show_points', True)}")

# ============================================================================
# 加载数据
# ============================================================================
def load_data():
    """智能查找并加载数据文件"""
    files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    files = [f for f in files if not f.startswith('_')]
    
    if not files:
        print(f"当前目录文件: {os.listdir('.')}")
        raise FileNotFoundError("未找到数据文件，请上传 .csv 或 .xlsx 文件")
    
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
# 智能识别列
# ============================================================================
# 识别数值列和分类列
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

print(f"数值列: {numeric_cols}")
print(f"分类列: {categorical_cols}")

# 确定 X轴（分类）、Y轴（数值）、分组列
x_col = config.get('x_column')
y_col = config.get('y_columns')
hue_col = config.get('group_column')

# 自动选择列
if not x_col:
    # 优先选择第一个分类列作为X轴
    if categorical_cols:
        x_col = categorical_cols[0]
    else:
        # 如果没有分类列，检查列名
        for col in df.columns:
            if any(kw in str(col).lower() for kw in ['组', 'group', 'category', '类别', 'type']):
                x_col = col
                break
        if not x_col and len(df.columns) >= 2:
            x_col = df.columns[0]

if not y_col:
    # 选择第一个数值列作为Y轴
    if numeric_cols:
        y_col = numeric_cols[0]
    else:
        # 尝试将某列转为数值
        for col in df.columns:
            if col != x_col:
                try:
                    df[col] = pd.to_numeric(df[col])
                    y_col = col
                    break
                except:
                    continue

if isinstance(y_col, list):
    y_col = y_col[0] if y_col else None

if not hue_col:
    # 选择第二个分类列作为hue
    remaining_cat = [c for c in categorical_cols if c != x_col]
    if remaining_cat:
        hue_col = remaining_cat[0]

print(f"使用列: X={x_col}, Y={y_col}, Hue={hue_col}")

if not x_col or not y_col:
    raise ValueError(f"无法识别数据列，需要至少一个分类列和一个数值列。当前列: {list(df.columns)}")

# ============================================================================
# 准备配色
# ============================================================================
# 预设配色方案
color_palettes = {
    'Set1': ['#E41A1C', '#377EB8', '#4DAF4A', '#984EA3', '#FF7F00', '#FFFF33'],
    'Set2': ['#66C2A5', '#FC8D62', '#8DA0CB', '#E78AC3', '#A6D854', '#FFD92F'],
    'Paired': ['#A6CEE3', '#1F78B4', '#B2DF8A', '#33A02C', '#FB9A99', '#E31A1C'],
    'jet': ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4'],
    'viridis': ['#440154', '#31688E', '#35B779', '#FDE725', '#26828E', '#1F9E89'],
    'plasma': ['#0D0887', '#7E03A8', '#CC4778', '#F89540', '#ED7953', '#FB9F3A'],
    'coolwarm': ['#3B4CC0', '#6788EE', '#9ABBFF', '#F7D4C9', '#F2A07B', '#B40426'],
    'RdYlBu': ['#D73027', '#F46D43', '#FDAE61', '#ABD9E9', '#74ADD1', '#4575B4'],
    'hot': ['#8B0000', '#FF0000', '#FF4500', '#FFA500', '#FFFF00', '#FFFFFF'],
}

palette = color_palettes.get(config['colormap'], color_palettes['Set1'])
if config.get('colors'):
    palette = config['colors']

# ============================================================================
# 绑制分组误差柱形图
# ============================================================================
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']))

# 设置误差类型
show_error = config.get('show_error', True)
errorbar_type = config.get('error_type', 'sd') if show_error else None

print(f"误差线设置: show_error={show_error}, error_type={errorbar_type}")

# 绑制柱形图
bar_kwargs = {
    'data': df,
    'x': x_col,
    'y': y_col,
    'palette': palette,
    'ax': ax,
    'edgecolor': 'white',
    'linewidth': 1.5,
    'width': config.get('bar_width', 0.8),
    'capsize': 0.15 if errorbar_type else 0,  # 加大误差线帽子
    'errorbar': errorbar_type,
    'err_kws': {'linewidth': 2, 'color': '#333333'} if errorbar_type else {},  # 加粗误差线
}

if hue_col:
    bar_kwargs['hue'] = hue_col

sns.barplot(**bar_kwargs)

# 添加数据点
if config.get('show_points', True):
    strip_kwargs = {
        'data': df,
        'x': x_col,
        'y': y_col,
        'color': '#333333',
        'alpha': 0.6,
        'size': config.get('point_size', 5),
        'ax': ax,
        'legend': False,
    }
    if hue_col:
        strip_kwargs['hue'] = hue_col
        strip_kwargs['dodge'] = True
        strip_kwargs['palette'] = ['#333333'] * 10
    
    sns.stripplot(**strip_kwargs)

# 设置标签
ax.set_xlabel(config['x_label'] or x_col, fontsize=12, fontweight='bold')
ax.set_ylabel(config['y_label'] or y_col, fontsize=12, fontweight='bold')

# 设置标题
if config['title']:
    ax.set_title(config['title'], fontsize=14, fontweight='bold', pad=10)

# 设置图例
if hue_col:
    ax.legend(title=hue_col, loc='upper right', frameon=True, fontsize=10)

# 网格线
ax.grid(True, linestyle='--', alpha=0.3, axis='y')
ax.set_axisbelow(True)

# 美化
sns.despine()

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"\n图表已保存: output.png")
