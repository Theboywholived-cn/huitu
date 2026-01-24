# 不同样式云雨图绘制示例
# 支持6种不同的云雨图样式
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
    'pastel': ['#66C2A5', '#FC8D62', '#E78AC3'],
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
        # 云雨图专属配置
        'raincloud_style': 1,     # 样式 1-6
        'show_box': True,         # 显示箱线图
        'show_points': False,     # 显示散点
        'show_violin': True,      # 显示小提琴
        'show_mean_line': False,  # 显示均值连线
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
print(f"配置: colormap={config['colormap']}, style={config.get('raincloud_style', 1)}")

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
        data = {
            '组别': ['setosa'] * n + ['versicolor'] * n + ['virginica'] * n,
            '数值': np.concatenate([
                np.random.normal(3.4, 0.4, n),
                np.random.normal(2.8, 0.3, n),
                np.random.normal(3.0, 0.35, n)
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
    # 优先找"组别"列或非数值列
    for col in df.columns:
        if '组' in col or 'group' in col.lower() or 'category' in col.lower():
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

# 优先使用colormap生成颜色，忽略空的colors列表
if config['colors'] and len(config['colors']) > 0:
    colors = config['colors']
else:
    colors = get_colors(config['colormap'], n_groups)
    
print(f"分组数: {n_groups}, 配色方案: {config['colormap']}, 颜色: {colors[:3]}...")

# ============================================================================
# 绑制云雨图
# ============================================================================
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']))

# 获取样式配置
style = config.get('raincloud_style', 1)
show_box = config.get('show_box', True)
show_points = config.get('show_points', False)
show_violin = config.get('show_violin', True)
show_mean_line = config.get('show_mean_line', False)

# 根据样式设置参数
# 样式1: 半小提琴 + 箱线图
# 样式2: 半小提琴 + 虚线统计标记
# 样式3: 半小提琴 + 散点
# 样式4: 半小提琴 + 箱线图 + 散点
# 样式5: 半小提琴 + 箱线图 + 密集散点
# 样式6: 半小提琴 + 箱线图 + 散点 + 均值连线

if style == 1:
    show_box = True
    show_points = False
    show_mean_line = False
elif style == 2:
    show_box = False
    show_points = False
    show_mean_line = False
elif style == 3:
    show_box = False
    show_points = True
    show_mean_line = False
elif style == 4:
    show_box = True
    show_points = True
    show_mean_line = False
elif style == 5:
    show_box = True
    show_points = True
    show_mean_line = False
elif style == 6:
    show_box = True
    show_points = True
    show_mean_line = True

print(f"样式{style}: box={show_box}, points={show_points}, mean_line={show_mean_line}")

# 准备数据
group_data = [df[df[x_col] == g][y_col].dropna().values for g in groups]
positions = np.arange(1, n_groups + 1)

# 绑制半小提琴图
if show_violin:
    parts = ax.violinplot(group_data, positions=positions, 
                          showmeans=False, showmedians=False, showextrema=False,
                          widths=0.6)
    
    for i, pc in enumerate(parts['bodies']):
        color = colors[i] if i < len(colors) else colors[i % len(colors)]
        pc.set_facecolor(color)
        pc.set_edgecolor('#333333')
        pc.set_linewidth(1)
        pc.set_alpha(0.7)
        
        # 只显示左半边（半小提琴）
        m = np.mean(pc.get_paths()[0].vertices[:, 0])
        pc.get_paths()[0].vertices[:, 0] = np.clip(pc.get_paths()[0].vertices[:, 0], -np.inf, m)

# 绑制箱线图
if show_box:
    box_positions = [p + 0.15 for p in positions]
    bp = ax.boxplot(group_data, positions=box_positions, widths=0.12,
                    patch_artist=True, showfliers=False,
                    medianprops=dict(color='white', linewidth=1.5),
                    whiskerprops=dict(color='#333333', linewidth=1),
                    capprops=dict(color='#333333', linewidth=1))
    
    for i, patch in enumerate(bp['boxes']):
        color = colors[i] if i < len(colors) else colors[i % len(colors)]
        patch.set_facecolor('#555555')
        patch.set_edgecolor('#333333')
        patch.set_alpha(0.8)

# 样式2: 虚线统计标记（中位数、四分位数）
if style == 2:
    for i, data in enumerate(group_data):
        pos = positions[i]
        q1, median, q3 = np.percentile(data, [25, 50, 75])
        # 绘制统计线
        ax.hlines(median, pos - 0.1, pos + 0.3, colors='#333333', linestyles='--', linewidth=1.5)
        ax.hlines(q1, pos - 0.05, pos + 0.25, colors='#333333', linestyles=':', linewidth=1)
        ax.hlines(q3, pos - 0.05, pos + 0.25, colors='#333333', linestyles=':', linewidth=1)

# 绑制散点
if show_points:
    for i, data in enumerate(group_data):
        pos = positions[i]
        color = colors[i] if i < len(colors) else colors[i % len(colors)]
        
        # 散点位置添加抖动
        if style == 5:
            # 样式5: 更密集的散点
            jitter = np.random.uniform(-0.08, 0.08, len(data))
            x_pts = pos + 0.25 + jitter
        else:
            jitter = np.random.uniform(-0.05, 0.05, len(data))
            x_pts = pos + 0.22 + jitter
        
        ax.scatter(x_pts, data, s=25, alpha=0.7, 
                   facecolors=color, edgecolors='white', linewidth=0.5)

# 绘制均值连线
if show_mean_line:
    means = [np.mean(data) for data in group_data]
    mean_positions = [p + 0.15 for p in positions]
    ax.plot(mean_positions, means, 'o-', color='#E64B35', 
            markersize=8, linewidth=2, markerfacecolor='#E64B35', 
            markeredgecolor='white', markeredgewidth=1.5)

# 设置坐标轴
ax.set_xticks(positions)
ax.set_xticklabels(groups, fontsize=11)
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
