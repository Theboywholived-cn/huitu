# 三元相气泡图绘制示例
import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
import matplotlib.patches as mpatches

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# 读取配置
# ============================================================================
def get_config():
    """获取图表配置"""
    default = {
        'colormap': 'viridis',
        'colors': None,
        'title': '三元相气泡图',
        'x_label': 'A',
        'y_label': 'B',
        'z_label': 'C',
        'show_legend': True,
        'show_grid': True,
        'fig_width': 10,
        'fig_height': 9,
        'dpi': 150,
        'marker_size': 100,
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
print(f"配置: colormap={config['colormap']}")

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
        n_points = 30
        a = np.random.uniform(0.1, 0.8, n_points)
        b = np.random.uniform(0.1, 0.8, n_points)
        c = 1 - a - b
        c = np.clip(c, 0.1, 0.8)
        total = a + b + c
        a, b, c = a/total, b/total, c/total
        sizes = np.random.uniform(100, 500, n_points)
        colors = np.random.uniform(0, 1, n_points)
        return pd.DataFrame({'A': a, 'B': b, 'C': c, 'Size': sizes, 'Color': colors})
    
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
# 找三个数值列作为三元坐标
numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

if len(numeric_cols) >= 3:
    a_col, b_col, c_col = numeric_cols[0], numeric_cols[1], numeric_cols[2]
    a = df[a_col].values
    b = df[b_col].values
    c = df[c_col].values
else:
    # 使用默认数据
    np.random.seed(42)
    n = len(df)
    a = np.random.uniform(0.1, 0.8, n)
    b = np.random.uniform(0.1, 0.8, n)
    c = 1 - a - b
    a_col, b_col, c_col = 'A', 'B', 'C'

# 归一化
total = a + b + c
a, b, c = a/total, b/total, c/total

# 大小列
if len(numeric_cols) >= 4:
    sizes = df[numeric_cols[3]].values
    # 归一化到合适范围
    sizes = (sizes - sizes.min()) / (sizes.max() - sizes.min() + 1e-10) * 400 + 50
else:
    sizes = np.ones(len(a)) * config['marker_size']

# 颜色列
if len(numeric_cols) >= 5:
    colors = df[numeric_cols[4]].values
else:
    colors = np.random.uniform(0, 1, len(a))

print(f"三元坐标: {a_col}, {b_col}, {c_col}")

# ============================================================================
# 坐标转换
# ============================================================================
def ternary_to_cartesian(a, b, c):
    """将三元坐标转换为笛卡尔坐标"""
    total = a + b + c
    a, b, c = a/total, b/total, c/total
    x = 0.5 * (2 * b + c)
    y = (np.sqrt(3) / 2) * c
    return x, y

# ============================================================================
# 绑制三元相气泡图
# ============================================================================
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']), dpi=config['dpi'])

# 绘制三角形边界
triangle = plt.Polygon([[0, 0], [1, 0], [0.5, np.sqrt(3)/2]], 
                       fill=False, edgecolor='black', linewidth=2)
ax.add_patch(triangle)

# 绘制网格线
if config['show_grid']:
    for i in range(1, 10):
        t = i / 10
        # 平行于底边
        x1, y1 = ternary_to_cartesian(1-t, t, 0)
        x2, y2 = ternary_to_cartesian(1-t, 0, t)
        ax.plot([x1, x2], [y1, y2], 'gray', linewidth=0.5, alpha=0.5)
        # 平行于左边
        x1, y1 = ternary_to_cartesian(0, t, 1-t)
        x2, y2 = ternary_to_cartesian(1-t, t, 0)
        ax.plot([x1, x2], [y1, y2], 'gray', linewidth=0.5, alpha=0.5)
        # 平行于右边
        x1, y1 = ternary_to_cartesian(t, 0, 1-t)
        x2, y2 = ternary_to_cartesian(0, t, 1-t)
        ax.plot([x1, x2], [y1, y2], 'gray', linewidth=0.5, alpha=0.5)

# 转换坐标
x_coords, y_coords = [], []
for i in range(len(a)):
    x, y = ternary_to_cartesian(a[i], b[i], c[i])
    x_coords.append(x)
    y_coords.append(y)

# 使用配置的 colormap
cmap = config['colormap']
# 确保是有效的 matplotlib colormap
valid_cmaps = ['jet', 'viridis', 'plasma', 'coolwarm', 'RdYlBu', 'hot', 'RdYlBu_r', 'coolwarm_r']
if cmap not in valid_cmaps:
    cmap = 'viridis'

scatter = ax.scatter(x_coords, y_coords, s=sizes, c=colors, cmap=cmap, 
                    alpha=0.7, edgecolors='white', linewidth=1)

# 添加颜色条
cbar = plt.colorbar(scatter, ax=ax, shrink=0.6, pad=0.05)
cbar.set_label('变量值', fontsize=11)

# 添加顶点标签
label_a = config.get('x_label') or a_col
label_b = config.get('y_label') or b_col
label_c = config.get('z_label') or c_col
ax.text(0, -0.05, label_a, fontsize=14, ha='center', fontweight='bold')
ax.text(1, -0.05, label_b, fontsize=14, ha='center', fontweight='bold')
ax.text(0.5, np.sqrt(3)/2 + 0.05, label_c, fontsize=14, ha='center', fontweight='bold')

# 添加刻度标签
for i in range(1, 10):
    t = i / 10
    # A轴刻度
    x, y = ternary_to_cartesian(1-t, t, 0)
    ax.text(x - 0.03, y - 0.03, f'{int(t*100)}', fontsize=8, ha='right')
    # B轴刻度  
    x, y = ternary_to_cartesian(0, 1-t, t)
    ax.text(x + 0.03, y, f'{int(t*100)}', fontsize=8, ha='left')
    # C轴刻度
    x, y = ternary_to_cartesian(t, 0, 1-t)
    ax.text(x - 0.02, y + 0.02, f'{int(t*100)}', fontsize=8, ha='right')

ax.set_xlim(-0.1, 1.1)
ax.set_ylim(-0.1, 1.0)
ax.set_aspect('equal')
ax.axis('off')

title = config['title'] or '三元相气泡图'
ax.set_title(title, fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"图表已保存: output.png")
