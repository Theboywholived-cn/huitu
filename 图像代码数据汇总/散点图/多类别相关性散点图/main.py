# 多类别相关性散点图
# 支持多组数据对比、误差线、R²和回归方程显示
import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

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
    'category': ['#4169E1', '#FFB347', '#90EE90', '#FF69B4', '#87CEEB', '#DDA0DD'],  # 蓝色、黄色等
}

# ============================================================================
# 读取配置
# ============================================================================
def get_config():
    """获取图表配置"""
    default = {
        'colormap': 'category',
        'colors': None,
        'title': '多类别相关性散点图',
        'x_label': 'Variable 01',
        'y_label': 'Variable 02',
        'show_legend': True,
        'show_grid': True,
        'fig_width': 10,
        'fig_height': 8,
        'dpi': 150,
        'marker_size': 8,
        # 相关性散点图专属配置
        'show_error': True,         # 显示误差线
        'show_regression': True,    # 显示回归线和方程
        'show_r2': True,            # 显示R²值
        'show_diagonal': True,      # 显示1:1对角线
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
print(f"配置: colormap={config['colormap']}, show_error={config.get('show_error', True)}")

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
        n = 50
        # 生成两组数据
        x1 = np.random.uniform(0, 1.6, n)
        y1 = 0.921 * x1 - 0.006 + np.random.normal(0, 0.15, n)
        err1 = np.random.uniform(0.05, 0.15, n)
        
        x2 = np.random.uniform(0, 1.6, n)
        y2 = 0.785 * x2 + 0.088 + np.random.normal(0, 0.12, n)
        err2 = np.random.uniform(0.05, 0.12, n)
        
        return pd.DataFrame({
            'X': np.concatenate([x1, x2]),
            'Y': np.concatenate([y1, y2]),
            'Y_err': np.concatenate([err1, err2]),
            'Group': ['Group1'] * n + ['Group2'] * n
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
# 找X列、Y列、误差列和分组列
x_col = None
y_col = None
y_err_col = None
group_col = None

numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
non_numeric_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]

# 查找分组列
for col in df.columns:
    col_lower = col.lower()
    if any(kw in col_lower for kw in ['group', 'category', 'type', 'class', '类别', '分组', '组']):
        group_col = col
        break

if not group_col and non_numeric_cols:
    group_col = non_numeric_cols[0]

# 查找X、Y列
for col in df.columns:
    col_lower = col.lower()
    if x_col is None and col in numeric_cols:
        if any(kw in col_lower for kw in ['x', 'var1', 'variable1', '变量1']):
            x_col = col
    if y_col is None and col in numeric_cols and col != x_col:
        if any(kw in col_lower for kw in ['y', 'var2', 'variable2', '变量2']):
            y_col = col

# 如果没找到，使用前两个数值列
if x_col is None and len(numeric_cols) >= 1:
    x_col = numeric_cols[0]
if y_col is None and len(numeric_cols) >= 2:
    y_col = numeric_cols[1]

# 查找误差列
for col in df.columns:
    col_lower = col.lower()
    if any(kw in col_lower for kw in ['err', 'error', 'std', 'se', '误差']):
        if 'y' in col_lower or y_col.lower() in col_lower:
            y_err_col = col
            break
        elif y_err_col is None:
            y_err_col = col

print(f"X列: {x_col}, Y列: {y_col}, 误差列: {y_err_col}, 分组列: {group_col}")

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
            return COLOR_PALETTES['category'][:count]

# ============================================================================
# 绑制多类别相关性散点图
# ============================================================================
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']), dpi=config['dpi'])

# 按分组绑制
if group_col and group_col in df.columns:
    groups = df[group_col].unique()
else:
    groups = ['All']
    df['_group'] = 'All'
    group_col = '_group'

# 获取颜色
if config['colors'] and len(config['colors']) > 0:
    colors = config['colors']
else:
    colors = get_colors(config['colormap'], len(groups))

print(f"分组数: {len(groups)}, 配色方案: {config['colormap']}")

# 存储回归信息用于显示
regression_info = []

for i, group in enumerate(groups):
    sub = df[df[group_col] == group]
    x = sub[x_col].values
    y = sub[y_col].values
    color = colors[i % len(colors)]
    
    # 计算回归
    if len(x) > 1 and config.get('show_regression', True):
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        r2 = r_value ** 2
        regression_info.append({
            'group': group,
            'slope': slope,
            'intercept': intercept,
            'r2': r2,
            'color': color
        })
    
    # 绘制误差线和散点
    if y_err_col and y_err_col in df.columns and config.get('show_error', True):
        y_err = sub[y_err_col].values
        ax.errorbar(x, y, yerr=y_err, fmt='o', color=color,
                   ecolor=color, elinewidth=1, capsize=2, capthick=1,
                   markersize=config['marker_size'], alpha=0.8, label=str(group),
                   markeredgecolor='white', markeredgewidth=0.5)
    else:
        ax.scatter(x, y, c=color, s=config['marker_size']**2, alpha=0.8, 
                  label=str(group), edgecolors='white', linewidth=0.5)

# 显示1:1对角线
if config.get('show_diagonal', True):
    all_x = df[x_col].values
    all_y = df[y_col].values
    min_val = min(all_x.min(), all_y.min())
    max_val = max(all_x.max(), all_y.max())
    margin = (max_val - min_val) * 0.1
    line_range = np.linspace(min_val - margin, max_val + margin, 100)
    ax.plot(line_range, line_range, '--', color='gray', linewidth=1.5, alpha=0.7, label='1:1 line')

# 显示R²和回归方程
if config.get('show_r2', True) and regression_info:
    text_y = 0.95
    for info in regression_info:
        r2_text = f"$R_{{{regression_info.index(info)+1}}}$ = {info['r2']:.2f}"
        sign = '+' if info['intercept'] >= 0 else ''
        eq_text = f"$y_{{{regression_info.index(info)+1}}}$ = {info['slope']:.3f}$x_{{{regression_info.index(info)+1}}}${sign}{info['intercept']:.3f}"
        
        ax.text(0.02, text_y, r2_text, transform=ax.transAxes, fontsize=11,
               color=info['color'], fontweight='bold', fontstyle='italic')
        ax.text(0.02, text_y - 0.05, eq_text, transform=ax.transAxes, fontsize=10,
               color=info['color'], fontstyle='italic')
        text_y -= 0.12

# 设置标签
ax.set_xlabel(config['x_label'] or x_col, fontsize=12, fontweight='bold')
ax.set_ylabel(config['y_label'] or y_col, fontsize=12, fontweight='bold')

# 标题
if config['title']:
    ax.set_title(config['title'], fontsize=14, fontweight='bold', pad=10)

# 图例
if config['show_legend'] and len(groups) > 1:
    ax.legend(loc='lower right', frameon=True, fancybox=True, fontsize=10)

# 网格
if config['show_grid']:
    ax.grid(True, linestyle='--', alpha=0.3)

# 设置坐标轴范围（保持相同比例）
all_x = df[x_col].values
all_y = df[y_col].values
min_val = min(all_x.min(), all_y.min())
max_val = max(all_x.max(), all_y.max())
margin = (max_val - min_val) * 0.1
ax.set_xlim(min_val - margin, max_val + margin)
ax.set_ylim(min_val - margin, max_val + margin)
ax.set_aspect('equal', adjustable='box')

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"图表已保存: output.png")
