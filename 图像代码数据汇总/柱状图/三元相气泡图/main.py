# 三元相气泡图绘制示例
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import RegularPolygon
import matplotlib.patches as mpatches
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
                    a, b, c = a/total, b/total, c/total
                    sizes = df['Size'].values * 10 if 'Size' in df.columns else np.random.uniform(100, 500, len(a))
                    colors = df['Color'].values if 'Color' in df.columns else np.random.uniform(0, 1, len(a))
                    return a, b, c, sizes, colors
            except Exception:
                pass
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
    return a, b, c, sizes, colors

# 加载数据
a, b, c, sizes, colors = load_data()

def ternary_to_cartesian(a, b, c):
    """将三元坐标转换为笛卡尔坐标"""
    total = a + b + c
    a, b, c = a/total, b/total, c/total
    x = 0.5 * (2 * b + c)
    y = (np.sqrt(3) / 2) * c
    return x, y

n_points = len(a)

# 创建图形
fig, ax = plt.subplots(figsize=(10, 9))

# 绘制三角形边界
triangle = plt.Polygon([[0, 0], [1, 0], [0.5, np.sqrt(3)/2]], 
                       fill=False, edgecolor='black', linewidth=2)
ax.add_patch(triangle)

# 绘制网格线
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

# 转换坐标并绘制气泡
x_coords, y_coords = [], []
for i in range(n_points):
    x, y = ternary_to_cartesian(a[i], b[i], c[i])
    x_coords.append(x)
    y_coords.append(y)

scatter = ax.scatter(x_coords, y_coords, s=sizes, c=colors, cmap='viridis', 
                    alpha=0.7, edgecolors='white', linewidth=1)

# 添加颜色条
cbar = plt.colorbar(scatter, ax=ax, shrink=0.6, pad=0.05)
cbar.set_label('变量值', fontsize=11)

# 添加顶点标签
ax.text(0, -0.05, 'A', fontsize=14, ha='center', fontweight='bold')
ax.text(1, -0.05, 'B', fontsize=14, ha='center', fontweight='bold')
ax.text(0.5, np.sqrt(3)/2 + 0.05, 'C', fontsize=14, ha='center', fontweight='bold')

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
ax.set_title('三元相气泡图', fontsize=14, pad=20)

plt.tight_layout()
plt.show()
