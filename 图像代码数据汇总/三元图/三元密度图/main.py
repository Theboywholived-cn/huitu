# 三元密度图绘制示例
# 支持密度热图 + 散点叠加、颜色条位置选择
import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
from scipy.ndimage import gaussian_filter

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# 预设配色方案
# ============================================================================
COLOR_PALETTES = {
    'viridis': 'viridis',
    'jet': 'jet',
    'plasma': 'plasma',
    'coolwarm': 'coolwarm',
    'RdYlBu': 'RdYlBu_r',
    'hot': 'hot',
    'YlOrRd': 'YlOrRd',
}

# 标记样式映射
MARKER_MAP = {
    'circle': 'o',
    'square': 's',
    'diamond': 'D',
    'triangle': '^',
    'star': '*',
    'plus': '+',
    'x': 'x',
}

# ============================================================================
# 读取配置
# ============================================================================
def get_config():
    """获取图表配置"""
    default = {
        'colormap': 'viridis',
        'colors': None,
        'title': '',
        'x_label': 'TiO2',         # 右下角（底边）
        'y_label': 'MgO',          # 左边
        'z_label': 'SiO2',         # 顶部
        'show_legend': True,
        'show_grid': True,
        'fig_width': 10,
        'fig_height': 10,
        'dpi': 150,
        'marker_size': 6,
        'marker_style': 'D',       # 菱形
        # 三元密度图专属配置
        'show_scatter': True,      # 显示散点
        'scatter_color': '#1f4e79', # 散点颜色（深蓝色）
        'colorbar_position': 'right', # 颜色条位置: right, bottom
        'colorbar_label': 'Relative point density\nfor ternary density plots',
        'density_sigma': 2,        # 密度平滑系数
        'grid_alpha': 0.3,         # 网格线透明度
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
print(f"配置: colormap={config['colormap']}, colorbar_position={config.get('colorbar_position', 'right')}")

# ============================================================================
# 坐标转换函数
# ============================================================================
def ternary_to_cartesian(a, b, c):
    """将三元坐标 (a=左, b=底, c=右) 转换为笛卡尔坐标
    
    三角形顶点：
    - 顶部 (a=1, b=0, c=0): (0.5, sqrt(3)/2)
    - 左下 (a=0, b=0, c=1): (0, 0)  
    - 右下 (a=0, b=1, c=0): (1, 0)
    """
    total = a + b + c
    a, b, c = a/total, b/total, c/total
    # 标准三元坐标转换
    x = 0.5 * (2 * b + a)
    y = (np.sqrt(3) / 2) * a
    return x, y

def is_in_triangle(x, y, margin=0.01):
    """检查点是否在三角形内"""
    h = np.sqrt(3) / 2
    if y < -margin or y > h + margin:
        return False
    # 左边界
    if x < y / np.sqrt(3) - margin:
        return False
    # 右边界
    if x > 1 - y / np.sqrt(3) + margin:
        return False
    return True

# ============================================================================
# 加载数据
# ============================================================================
def load_data():
    """智能查找并加载数据文件"""
    files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    files = [f for f in files if not f.startswith('_')]
    
    if not files:
        # 内置示例数据 - 模拟真实的三元密度分布
        np.random.seed(42)
        n = 1000
        
        # 主要聚集区域（模拟图中的分布）
        a_list, b_list, c_list = [], [], []
        
        # 高密度区域（右下角附近，TiO2高，SiO2和MgO低）
        for _ in range(600):
            a = np.random.exponential(0.1)  # SiO2 (顶部)
            b = np.random.normal(0.8, 0.15) # TiO2 (右下)
            c = np.random.exponential(0.15) # MgO (左下)
            a_list.append(max(0.01, a))
            b_list.append(max(0.01, b))
            c_list.append(max(0.01, c))
        
        # 分散的点
        for _ in range(400):
            a = np.random.uniform(0.05, 0.6)
            b = np.random.uniform(0.2, 0.9)
            c = np.random.uniform(0.05, 0.5)
            a_list.append(a)
            b_list.append(b)
            c_list.append(c)
        
        return pd.DataFrame({
            'SiO2': a_list,
            'TiO2': b_list,
            'MgO': c_list,
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
# 确定三元坐标列
# ============================================================================
cols = list(df.columns)
numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]

# 尝试匹配列名
top_col = None    # 顶部顶点（SiO2）
right_col = None  # 右下顶点（TiO2） 
left_col = None   # 左下顶点（MgO）

for col in numeric_cols:
    col_lower = col.lower()
    if top_col is None and any(kw in col_lower for kw in ['sio', 'si', 'a', 'top', '顶']):
        top_col = col
    elif right_col is None and any(kw in col_lower for kw in ['tio', 'ti', 'b', 'right', '右']):
        right_col = col
    elif left_col is None and any(kw in col_lower for kw in ['mgo', 'mg', 'c', 'left', '左']):
        left_col = col

# 如果没找到，使用前三个数值列
if len(numeric_cols) >= 3:
    if top_col is None:
        top_col = numeric_cols[0]
    if right_col is None:
        remaining = [c for c in numeric_cols if c != top_col]
        right_col = remaining[0] if remaining else numeric_cols[1]
    if left_col is None:
        remaining = [c for c in numeric_cols if c not in [top_col, right_col]]
        left_col = remaining[0] if remaining else numeric_cols[2]

print(f"顶部列: {top_col}, 右下列: {right_col}, 左下列: {left_col}")

# 提取数据并归一化
data_top = df[top_col].values
data_right = df[right_col].values
data_left = df[left_col].values

# 归一化到 0-1
total = data_top + data_right + data_left
data_top = data_top / total
data_right = data_right / total
data_left = data_left / total

# 转换为笛卡尔坐标
x_data = []
y_data = []
for i in range(len(data_top)):
    x, y = ternary_to_cartesian(data_top[i], data_right[i], data_left[i])
    x_data.append(x)
    y_data.append(y)
x_data = np.array(x_data)
y_data = np.array(y_data)

# ============================================================================
# 创建图形
# ============================================================================
fig, ax = plt.subplots(figsize=(config['fig_width'], config['fig_height']), dpi=config['dpi'])

# ============================================================================
# 计算密度热图
# ============================================================================
grid_size = 200
h = np.sqrt(3) / 2

# 创建网格
x_grid = np.linspace(0, 1, grid_size)
y_grid = np.linspace(0, h, grid_size)

# 使用直方图估计密度
H, xedges, yedges = np.histogram2d(x_data, y_data, bins=100, 
                                    range=[[0, 1], [0, h]])
H = gaussian_filter(H.T, sigma=config.get('density_sigma', 2))

# 归一化密度到 0-1
H_max = np.nanmax(H)
if H_max > 0:
    H = H / H_max

# 裁剪三角形外的区域
for i in range(H.shape[0]):
    for j in range(H.shape[1]):
        x_center = (xedges[j] + xedges[j+1]) / 2
        y_center = (yedges[i] + yedges[i+1]) / 2
        if not is_in_triangle(x_center, y_center, margin=0.02):
            H[i, j] = np.nan

# ============================================================================
# 绘制密度热图
# ============================================================================
extent = [0, 1, 0, h]
cmap_name = COLOR_PALETTES.get(config['colormap'], config['colormap'])
im = ax.imshow(H, extent=extent, origin='lower', cmap=cmap_name, 
              aspect='equal', interpolation='bilinear', alpha=0.95,
              vmin=0, vmax=1)

# ============================================================================
# 绘制散点
# ============================================================================
if config.get('show_scatter', True):
    scatter_color = config.get('scatter_color', '#1f4e79')
    marker_name = config.get('marker_style', 'diamond')
    marker = MARKER_MAP.get(marker_name, marker_name)  # 转换标记名称
    ax.scatter(x_data, y_data, s=config['marker_size']**2, c=scatter_color,
              marker=marker, edgecolors='none', alpha=0.7, zorder=3)

# ============================================================================
# 绘制三角形边界
# ============================================================================
triangle = plt.Polygon([[0, 0], [1, 0], [0.5, h]], 
                       fill=False, edgecolor='black', linewidth=2, zorder=5)
ax.add_patch(triangle)

# ============================================================================
# 绘制网格线
# ============================================================================
if config.get('show_grid', True):
    grid_alpha = config.get('grid_alpha', 0.3)
    
    # 绘制平行于各边的网格线
    for i in range(1, 10):
        t = i / 10
        
        # 平行于底边的线（从左边到右边）
        x1 = t * 0.5
        y1 = t * h
        x2 = 1 - t * 0.5
        y2 = t * h
        ax.plot([x1, x2], [y1, y2], 'gray', linewidth=0.8, alpha=grid_alpha, zorder=2)
        
        # 平行于左边的线（从底边到右边）
        x1 = t
        y1 = 0
        x2 = 0.5 + t * 0.5
        y2 = (1 - t) * h
        ax.plot([x1, x2], [y1, y2], 'gray', linewidth=0.8, alpha=grid_alpha, zorder=2)
        
        # 平行于右边的线（从底边到左边）
        x1 = 1 - t
        y1 = 0
        x2 = 0.5 - t * 0.5
        y2 = (1 - t) * h
        ax.plot([x1, x2], [y1, y2], 'gray', linewidth=0.8, alpha=grid_alpha, zorder=2)

# ============================================================================
# 添加刻度标签
# ============================================================================
tick_values = [0, 0.2, 0.4, 0.6, 0.8, 1.0]

# 底边刻度（TiO2 / right_col）- 从左到右 0->1
for t in tick_values:
    x = t
    y = -0.04
    ax.text(x, y, f'{t:.1f}', ha='center', va='top', fontsize=10)

# 左边刻度（MgO / left_col）- 从底（0）到顶（1）
for t in tick_values:
    # 在左边沿着从底点到顶点的方向
    x = 0.5 * (1-t) - 0.04  # t=0时在底部(x=0.5-0.04), t=1时在顶点附近
    y = (1-t) * h  # t=0时y=h(顶部), t=1时y=0(底部)，需要反过来
    # 修正：t=0对应底部(0,0)，t=1对应中途
    x = t * 0.5 - 0.04
    y = t * h
    ax.text(x, y, f'{1-t:.1f}', ha='right', va='center', fontsize=10, rotation=60)

# 右边刻度（SiO2 / top_col）- 从顶（0）到底（1）
for t in tick_values:
    x = 1 - t * 0.5 + 0.04
    y = t * h
    ax.text(x, y, f'{1-t:.1f}', ha='left', va='center', fontsize=10, rotation=-60)

# ============================================================================
# 添加轴标签
# ============================================================================
# 使用配置中的标签或列名
top_label = config.get('z_label') or top_col or 'SiO2'
right_label = config.get('x_label') or right_col or 'TiO2'
left_label = config.get('y_label') or left_col or 'MgO'

# 顶部标签
ax.text(0.5, h + 0.08, top_label, ha='center', va='bottom', fontsize=14, fontweight='bold')

# 左下标签（MgO）- 旋转60度
ax.text(-0.12, h/2, left_label, ha='center', va='center', fontsize=14, 
       fontweight='bold', rotation=60)

# 右下标签（TiO2）- 旋转-60度
ax.text(1.12, h/2, right_label, ha='center', va='center', fontsize=14,
       fontweight='bold', rotation=-60)

# ============================================================================
# 添加颜色条
# ============================================================================
colorbar_pos = config.get('colorbar_position', 'right')
colorbar_label = config.get('colorbar_label', 'Relative point density\nfor ternary density plots')

if colorbar_pos == 'bottom':
    # 底部水平颜色条
    cax = fig.add_axes([0.2, 0.02, 0.6, 0.03])  # [left, bottom, width, height]
    cbar = plt.colorbar(im, cax=cax, orientation='horizontal')
    cbar.set_label(colorbar_label.replace('\n', ' '), fontsize=11)
    cbar.ax.tick_params(labelsize=10)
else:
    # 右侧垂直颜色条
    cbar = plt.colorbar(im, ax=ax, shrink=0.7, pad=0.12, aspect=25)
    cbar.set_label(colorbar_label, fontsize=11, rotation=270, labelpad=20)
    cbar.ax.tick_params(labelsize=10)

# ============================================================================
# 设置图形范围和样式
# ============================================================================
ax.set_xlim(-0.15, 1.15)
ax.set_ylim(-0.12, h + 0.15)
ax.set_aspect('equal')
ax.axis('off')

# 添加标题
if config.get('title'):
    ax.set_title(config['title'], fontsize=14, fontweight='bold', pad=25)

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"图表已保存: output.png")
