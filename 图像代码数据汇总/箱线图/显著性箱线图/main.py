# 带显著性标注箱线图绘制示例
# 支持多组比较、显著性检验方法选择、散点叠加
import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# 预设配色方案
# ============================================================================
COLOR_PALETTES = {
    'jet': ['#2ECC71', '#3498DB', '#E91E63', '#F1C40F', '#9B59B6', '#1ABC9C'],
    'viridis': ['#440154', '#31688E', '#35B779', '#FDE725', '#26828E', '#1F9E89'],
    'plasma': ['#0D0887', '#7E03A8', '#CC4778', '#F89540', '#ED7953', '#FB9F3A'],
    'coolwarm': ['#3B4CC0', '#6788EE', '#9ABBFF', '#F7D4C9', '#F2A07B', '#B40426'],
    'RdYlBu': ['#D73027', '#F46D43', '#FDAE61', '#ABD9E9', '#74ADD1', '#4575B4'],
    'pastel': ['#2ECC71', '#3498DB', '#E91E63', '#F1C40F', '#9B59B6', '#E67E22'],
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
        'x_label': 'Time',
        'y_label': 'Values',
        'show_legend': True,
        'show_grid': True,
        'fig_width': 10,
        'fig_height': 8,
        'dpi': 150,
        'marker_size': 8,
        # 显著性箱线图专属配置
        'show_points': True,         # 显示散点
        'show_significance': True,   # 显示显著性标注
        'test_method': 'mww',        # 检验方法: ttest, mww (Mann-Whitney-Wilcoxon)
        'significance_pairs': None,  # 指定比较的组对，None表示与第一组比较
        'box_width': 0.6,            # 箱子宽度
        'point_alpha': 0.7,          # 散点透明度
        'jitter_amount': 0.15,       # 散点抖动量
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
print(f"配置: colormap={config['colormap']}, test_method={config.get('test_method', 'mww')}")

# ============================================================================
# 加载数据
# ============================================================================
def load_data():
    """智能查找并加载数据文件"""
    files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    files = [f for f in files if not f.startswith('_')]
    
    if not files:
        # 内置示例数据 - 模拟图片中的数据
        np.random.seed(42)
        n_per_group = 50
        
        return pd.DataFrame({
            'Time': np.repeat(['Sun', 'Thur', 'Fri', 'Sat'], n_per_group),
            'Values': np.concatenate([
                np.random.normal(20, 8, n_per_group),   # Sun
                np.random.normal(18, 7, n_per_group),   # Thur
                np.random.normal(16, 8, n_per_group),   # Fri
                np.random.normal(20, 10, n_per_group),  # Sat
            ])
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
# 确定分组列和数值列
# ============================================================================
group_col = None
value_col = None

for col in df.columns:
    if not pd.api.types.is_numeric_dtype(df[col]):
        if group_col is None:
            group_col = col
    else:
        if value_col is None:
            value_col = col

# 如果没有分类列，使用第一列
if group_col is None:
    group_col = df.columns[0]
if value_col is None:
    numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    value_col = numeric_cols[0] if numeric_cols else df.columns[1]

print(f"分组列: {group_col}, 数值列: {value_col}")

groups = df[group_col].unique()
n_groups = len(groups)

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
positions = np.arange(n_groups)

# 绑制每个组的箱线图
box_data = [df[df[group_col] == g][value_col].dropna().values for g in groups]

# 绑制箱线图
bp = ax.boxplot(box_data, positions=positions, widths=box_width, patch_artist=True,
                medianprops=dict(color='#444444', linewidth=1.5),
                whiskerprops=dict(color='#444444', linewidth=1.2),
                capprops=dict(color='#444444', linewidth=1.2),
                flierprops=dict(marker='o', markerfacecolor='none', markeredgecolor='#444444', 
                               markersize=5, alpha=0.5))

# 设置箱子颜色
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)
    patch.set_edgecolor('#444444')
    patch.set_linewidth(1.2)
    patch.set_alpha(0.9)

# ============================================================================
# 添加散点
# ============================================================================
if config.get('show_points', True):
    jitter = config.get('jitter_amount', 0.15)
    point_alpha = config.get('point_alpha', 0.7)
    marker_size = config.get('marker_size', 8)
    
    for i, (g, color) in enumerate(zip(groups, colors)):
        values = df[df[group_col] == g][value_col].dropna().values
        # 散点在箱子右侧，带抖动
        x_jitter = np.random.uniform(0.02, jitter, len(values)) + i + box_width/2 - 0.05
        ax.scatter(x_jitter, values, c=color, s=marker_size**2, alpha=point_alpha,
                  edgecolors='#444444', linewidths=0.3, zorder=3)

# ============================================================================
# 显著性检验和标注
# ============================================================================
if config.get('show_significance', True):
    test_method = config.get('test_method', 'mww')
    
    def perform_test(data1, data2, method='mww'):
        """执行统计检验"""
        if method == 'ttest':
            stat, p_val = stats.ttest_ind(data1, data2)
            method_name = "t-test"
        else:  # mww (Mann-Whitney-Wilcoxon)
            stat, p_val = stats.mannwhitneyu(data1, data2, alternative='two-sided')
            method_name = "M.W.W."
        return p_val, method_name
    
    def add_significance_annotation(x1, x2, y, p_val, method_name):
        """添加显著性标注"""
        # 绑制连接线
        h = 2  # 线条高度
        ax.plot([x1, x1], [y, y + h], 'k-', linewidth=1)
        ax.plot([x1, x2], [y + h, y + h], 'k-', linewidth=1)
        ax.plot([x2, x2], [y + h, y], 'k-', linewidth=1)
        
        # 格式化 p 值
        if p_val < 0.001:
            p_text = f"{method_name} p < 0.001"
        elif p_val < 0.05:
            p_text = f"{method_name} p ≤ 0.05"
        else:
            p_text = f"{method_name} p = {p_val:.2f}"
        
        # 添加文字
        ax.text((x1 + x2) / 2, y + h + 0.5, p_text, 
               ha='center', va='bottom', fontsize=9, fontweight='normal')
    
    # 确定比较对
    # 默认：第一组与其他组比较，以及相邻组之间比较
    y_max = max([d.max() for d in box_data if len(d) > 0])
    current_y = y_max + 5
    y_step = 8
    
    # 比较对列表：(index1, index2)
    comparison_pairs = []
    
    # 添加一些典型的比较对（模拟图片中的标注）
    if n_groups >= 2:
        comparison_pairs.append((0, 1))  # 第一组 vs 第二组
    if n_groups >= 3:
        comparison_pairs.append((1, 2))  # 第二组 vs 第三组
    if n_groups >= 4:
        comparison_pairs.append((1, 3))  # 第二组 vs 第四组
    
    # 按照比较对的跨度排序（跨度大的在上面）
    comparison_pairs.sort(key=lambda x: abs(x[1] - x[0]), reverse=True)
    
    for idx1, idx2 in comparison_pairs:
        if idx1 < len(box_data) and idx2 < len(box_data):
            data1 = box_data[idx1]
            data2 = box_data[idx2]
            if len(data1) > 0 and len(data2) > 0:
                p_val, method_name = perform_test(data1, data2, test_method)
                add_significance_annotation(idx1, idx2, current_y, p_val, method_name)
                current_y += y_step

# ============================================================================
# 设置坐标轴和标签
# ============================================================================
ax.set_xticks(positions)
ax.set_xticklabels(groups, fontsize=11)

x_label = config.get('x_label') or group_col
y_label = config.get('y_label') or value_col
ax.set_xlabel(x_label, fontsize=12, fontweight='bold')
ax.set_ylabel(y_label, fontsize=12, fontweight='bold')

if config.get('title'):
    ax.set_title(config['title'], fontsize=14, fontweight='bold', pad=15)

# 网格
if config.get('show_grid', True):
    ax.grid(True, linestyle='--', alpha=0.3, axis='y')
    ax.set_axisbelow(True)

# 设置Y轴范围，留出标注空间
y_min = min([d.min() for d in box_data if len(d) > 0])
y_max_data = max([d.max() for d in box_data if len(d) > 0])
if config.get('show_significance', True):
    ax.set_ylim(y_min - 2, current_y + 5)
else:
    ax.set_ylim(y_min - 2, y_max_data + 5)

# 移除顶部和右侧边框
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"图表已保存: output.png")
