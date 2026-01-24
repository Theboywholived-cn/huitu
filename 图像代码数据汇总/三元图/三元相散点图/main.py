# 三元相散点图绘制示例
# 支持多数据组散点和颜色分级散点两种模式
import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ternary

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
    'jet': ['#4169E1', '#4DBBD5', '#E64B35', '#F39B7F', '#8491B4'],
    'viridis': ['#440154', '#31688E', '#35B779', '#FDE725'],
    'plasma': ['#0D0887', '#7E03A8', '#CC4778', '#F89540'],
    'ternary': ['#4169E1', '#FF69B4'],  # 参考图片配色：蓝色圆形、粉色三角
    'rainbow': ['#2ECC71', '#3498DB', '#E91E8C', '#F5A623', '#9B59B6'],  # 彩虹5色
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
        'colormap': 'ternary',
        'colors': None,
        'title': '',
        'x_label': 'Variable 1',   # 底边标签
        'y_label': 'Variable 2',   # 左边标签
        'z_label': 'Variable 3',   # 右边标签
        'show_legend': True,
        'show_grid': True,
        'fig_width': 10,
        'fig_height': 8,
        'dpi': 150,
        # 三元图专属配置
        'ternary_mode': 'group',   # 模式: group(分组散点), color(颜色映射)
        'marker_size': 80,         # 散点大小
        'point_size': 5,           # 兼容
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
print(f"配置: colormap={config['colormap']}, mode={config.get('ternary_mode', 'group')}")

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
        n = 50
        # 生成两组数据
        data = {
            'Variable1': np.random.dirichlet([2, 2, 2], n)[:, 0],
            'Variable2': np.random.dirichlet([2, 2, 2], n)[:, 1],
            'Variable3': np.random.dirichlet([2, 2, 2], n)[:, 2],
            'Type': ['Test 01'] * 25 + ['Test 02'] * 25,
            'Size Value': np.random.rand(n)
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
# 智能识别三元图的三个变量列
var_cols = []
numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

# 尝试按名称匹配
for pattern in [['A', 'B', 'C'], ['Variable1', 'Variable2', 'Variable3'], 
                ['Var1', 'Var2', 'Var3'], ['v1', 'v2', 'v3']]:
    matched = [c for c in df.columns if c in pattern or any(p.lower() in c.lower() for p in pattern)]
    if len(matched) >= 3:
        var_cols = matched[:3]
        break

# 如果没匹配到，使用前三个数值列
if len(var_cols) < 3:
    var_cols = numeric_cols[:3]

if len(var_cols) < 3:
    raise ValueError("需要至少3个数值列来绑制三元图")

print(f"三元变量列: {var_cols}")

# 识别分组列（用于分组模式）
group_col = None
for col in df.columns:
    if col not in var_cols and not pd.api.types.is_numeric_dtype(df[col]):
        group_col = col
        break
    if col.lower() in ['type', 'group', '组', '类型', '分组', 'category']:
        group_col = col
        break

# 识别数值映射列（用于颜色模式）
value_col = None
for col in df.columns:
    if col not in var_cols and pd.api.types.is_numeric_dtype(df[col]):
        value_col = col
        break

print(f"分组列: {group_col}, 数值映射列: {value_col}")

# ============================================================================
# 确定绑制模式
# ============================================================================
mode = config.get('ternary_mode', 'group')
if mode == 'auto':
    # 自动判断：如果有分组列用分组模式，否则用颜色模式
    mode = 'group' if group_col else 'color'

# ============================================================================
# 获取配色
# ============================================================================
def get_colors(colormap_name, count):
    if colormap_name in COLOR_PALETTES:
        palette = COLOR_PALETTES[colormap_name]
        return [palette[i % len(palette)] for i in range(count)]
    else:
        try:
            import matplotlib.cm as cm
            cmap = cm.get_cmap(colormap_name)
            return [cmap(i / max(count - 1, 1)) for i in range(count)]
        except:
            return COLOR_PALETTES['jet'][:count]

# ============================================================================
# 绑制三元图
# ============================================================================
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']))

# 创建三元图
scale = 1.0
tax = ternary.TernaryAxesSubplot(ax=ax, scale=scale)

# 绘制边界和网格
tax.boundary(linewidth=2.0)
if config['show_grid']:
    tax.gridlines(color="gray", multiple=0.1, linewidth=0.5, alpha=0.5)

# 设置刻度
tax.ticks(axis='lbr', linewidth=1, multiple=0.2, offset=0.02, tick_formats="%.1f")

# 设置轴标签
tax.left_axis_label(config['y_label'], fontsize=14, fontweight='bold', offset=0.14)
tax.right_axis_label(config.get('z_label', 'Variable 3'), fontsize=14, fontweight='bold', offset=0.14)
tax.bottom_axis_label(config['x_label'], fontsize=14, fontweight='bold', offset=0.02)

# 设置顶点标签
tax.left_corner_label("Left", fontsize=10, offset=0.02)
tax.right_corner_label("Right", fontsize=10, offset=0.02)
tax.top_corner_label("Top", fontsize=10, offset=0.05)

# 获取三元坐标数据
v1 = df[var_cols[0]].values
v2 = df[var_cols[1]].values
v3 = df[var_cols[2]].values

# 归一化（确保和为1）
total = v1 + v2 + v3
v1, v2, v3 = v1 / total, v2 / total, v3 / total

# 转换为三元图坐标格式 (bottom, left, right) = (v1, v2, v3)
# python-ternary使用的是 (bottom, right, left) 顺序，需要确认

if mode == 'group' and group_col:
    # 分组模式：不同组使用不同颜色和标记
    groups = df[group_col].unique()
    n_groups = len(groups)
    
    if config['colors'] and len(config['colors']) > 0:
        colors = config['colors']
    else:
        colors = get_colors(config['colormap'], n_groups)
    
    markers = ['o', '^', 's', 'D', 'v', 'p', 'h', '*']
    
    for i, group in enumerate(groups):
        mask = df[group_col] == group
        points = [(v1[j], v2[j], v3[j]) for j in range(len(v1)) if mask.iloc[j]]
        
        color = colors[i % len(colors)]
        marker = markers[i % len(markers)]
        
        tax.scatter(points, marker=marker, color=color, 
                   s=config.get('marker_size', 80), 
                   label=str(group), edgecolors='white', linewidth=0.5, alpha=0.8)
    
    if config['show_legend']:
        tax.legend(title='Type', loc='upper right', fontsize=10)

else:
    # 颜色映射模式：使用数值列映射颜色
    points = [(v1[i], v2[i], v3[i]) for i in range(len(v1))]
    
    if value_col:
        values = df[value_col].values
        # 分档颜色
        bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        bin_labels = ['0.0~0.2', '0.2~0.4', '0.4~0.6', '0.6~0.8', '0.8~1.0']
        colors = get_colors('rainbow', 5)
        
        for i in range(len(bins) - 1):
            mask = (values >= bins[i]) & (values < bins[i + 1])
            if i == len(bins) - 2:  # 最后一档包含上界
                mask = (values >= bins[i]) & (values <= bins[i + 1])
            
            bin_points = [(v1[j], v2[j], v3[j]) for j in range(len(v1)) if mask[j]]
            if bin_points:
                tax.scatter(bin_points, marker='o', color=colors[i],
                           s=config.get('marker_size', 80),
                           label=bin_labels[i], edgecolors='white', linewidth=0.5, alpha=0.8)
        
        if config['show_legend']:
            tax.legend(title='Size Value', loc='upper right', fontsize=10)
    else:
        # 无数值列，单色绘制
        if config['colors'] and len(config['colors']) > 0:
            color = config['colors'][0]
        else:
            color = '#4169E1'
        tax.scatter(points, marker='o', color=color,
                   s=config.get('marker_size', 80),
                   edgecolors='white', linewidth=0.5, alpha=0.8)

# 标题
if config['title']:
    tax.set_title(config['title'], fontsize=14, fontweight='bold', pad=20)

# 清除matplotlib默认轴
tax.clear_matplotlib_ticks()
ax.axis('off')

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"\n图表已保存: output.png")
