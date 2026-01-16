# 三元密度图绘制示例
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    """加载外部数据或返回内置示例数据"""
    for fname in ['示范数据.xlsx', '示范数据.csv']:
        if os.path.exists(fname):
            try:
                df = pd.read_excel(fname) if fname.endswith('.xlsx') else pd.read_csv(fname)
                if 'A' in df.columns and 'B' in df.columns and 'C' in df.columns:
                    a, b, c = df['A'].values, df['B'].values, df['C'].values
                    total = a + b + c
                    return a/total, b/total, c/total
            except Exception:
                pass
    # 内置示例数据 - 多个聚类中心
    np.random.seed(42)
    n = 500
    centers = [(0.5, 0.3, 0.2), (0.3, 0.5, 0.2), (0.2, 0.3, 0.5)]
    data_a, data_b, data_c = [], [], []
    for center in centers:
        n_cluster = n // 3
        a = np.random.normal(center[0], 0.1, n_cluster)
        b = np.random.normal(center[1], 0.1, n_cluster)
        c = np.random.normal(center[2], 0.1, n_cluster)
        a, b, c = np.abs(a), np.abs(b), np.abs(c)
        total = a + b + c
        data_a.extend(a / total)
        data_b.extend(b / total)
        data_c.extend(c / total)
    return np.array(data_a), np.array(data_b), np.array(data_c)

# 加载数据
data_a, data_b, data_c = load_data()

def ternary_to_cartesian(a, b, c):
    """将三元坐标转换为笛卡尔坐标"""
    total = a + b + c
    a, b, c = a/total, b/total, c/total
    x = 0.5 * (2 * b + c)
    y = (np.sqrt(3) / 2) * c
    return x, y

def is_in_triangle(x, y):
    """检查点是否在三角形内"""
    if y < 0 or y > np.sqrt(3) / 2:
        return False
    if x < y / np.sqrt(3) or x > 1 - y / np.sqrt(3):
        return False
    return True

# 创建图形
fig, ax = plt.subplots(figsize=(10, 9))

# 创建密度网格
grid_size = 100
x_grid = np.linspace(0, 1, grid_size)
y_grid = np.linspace(0, np.sqrt(3) / 2, grid_size)
X, Y = np.meshgrid(x_grid, y_grid)
density = np.zeros_like(X)

# 计算每个数据点的贡献
x_data = [ternary_to_cartesian(data_a[i], data_b[i], data_c[i])[0] for i in range(len(data_a))]
y_data = [ternary_to_cartesian(data_a[i], data_b[i], data_c[i])[1] for i in range(len(data_a))]

# 使用直方图估计密度
H, xedges, yedges = np.histogram2d(x_data, y_data, bins=50, range=[[0, 1], [0, np.sqrt(3)/2]])
H = gaussian_filter(H.T, sigma=2)

# 裁剪三角形外的区域
for i in range(H.shape[0]):
    for j in range(H.shape[1]):
        x_center = (xedges[j] + xedges[j+1]) / 2
        y_center = (yedges[i] + yedges[i+1]) / 2
        if not is_in_triangle(x_center, y_center):
            H[i, j] = np.nan

# 绘制密度图
extent = [0, 1, 0, np.sqrt(3)/2]
im = ax.imshow(H, extent=extent, origin='lower', cmap='YlOrRd', 
              aspect='equal', interpolation='bilinear', alpha=0.9)

# 添加等高线
levels = np.linspace(np.nanmin(H), np.nanmax(H), 10)[1:]
cs = ax.contour(H, levels=levels, extent=extent, colors='white', 
               linewidths=0.5, alpha=0.5)

# 绘制三角形边界
triangle = plt.Polygon([[0, 0], [1, 0], [0.5, np.sqrt(3)/2]], 
                       fill=False, edgecolor='black', linewidth=2)
ax.add_patch(triangle)

# 添加网格线
for i in range(1, 10):
    t = i / 10
    x1, y1 = ternary_to_cartesian(1-t, t, 0)
    x2, y2 = ternary_to_cartesian(1-t, 0, t)
    ax.plot([x1, x2], [y1, y2], 'gray', linewidth=0.5, alpha=0.3)
    x1, y1 = ternary_to_cartesian(0, t, 1-t)
    x2, y2 = ternary_to_cartesian(1-t, t, 0)
    ax.plot([x1, x2], [y1, y2], 'gray', linewidth=0.5, alpha=0.3)

# 添加颜色条
cbar = plt.colorbar(im, ax=ax, shrink=0.6, pad=0.05)
cbar.set_label('密度', fontsize=11)

# 添加顶点标签
ax.text(0, -0.05, 'A', fontsize=14, ha='center', fontweight='bold')
ax.text(1, -0.05, 'B', fontsize=14, ha='center', fontweight='bold')
ax.text(0.5, np.sqrt(3)/2 + 0.05, 'C', fontsize=14, ha='center', fontweight='bold')

ax.set_xlim(-0.1, 1.1)
ax.set_ylim(-0.1, 1.0)
ax.set_aspect('equal')
ax.axis('off')
ax.set_title('三元密度图绘制示例', fontsize=14, pad=20)

plt.tight_layout()
plt.show()
