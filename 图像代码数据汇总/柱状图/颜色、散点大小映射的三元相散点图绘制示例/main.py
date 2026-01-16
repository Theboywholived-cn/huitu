# 颜色、散点大小映射的三元相散点图绘制示例
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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
                    color_values = df['Color'].values if 'Color' in df.columns else a * b + np.random.uniform(0, 0.1, len(a))
                    size_values = df['Size'].values if 'Size' in df.columns else c * 300 + 50
                    return a, b, c, color_values, size_values
            except Exception:
                pass
    # 内置示例数据
    np.random.seed(42)
    n = 50
    a = np.random.uniform(0.1, 0.8, n)
    b = np.random.uniform(0.1, 0.8, n)
    c = 1 - a - b
    c = np.clip(c, 0.1, 0.8)
    total = a + b + c
    a, b, c = a/total, b/total, c/total
    color_values = a * b + np.random.uniform(0, 0.1, n)
    size_values = c * 300 + 50
    return a, b, c, color_values, size_values

# 加载数据
a, b, c, color_values, size_values = load_data()
n = len(a)

def ternary_to_cartesian(a, b, c):
    """将三元坐标转换为笛卡尔坐标"""
    total = a + b + c
    a, b, c = a/total, b/total, c/total
    x = 0.5 * (2 * b + c)
    y = (np.sqrt(3) / 2) * c
    return x, y

def draw_ternary_base(ax):
    """绘制三元图基础框架"""
    triangle = plt.Polygon([[0, 0], [1, 0], [0.5, np.sqrt(3)/2]], 
                          fill=False, edgecolor='black', linewidth=2)
    ax.add_patch(triangle)
    
    for i in range(1, 10):
        t = i / 10
        x1, y1 = ternary_to_cartesian(1-t, t, 0)
        x2, y2 = ternary_to_cartesian(1-t, 0, t)
        ax.plot([x1, x2], [y1, y2], 'gray', linewidth=0.5, alpha=0.3)
        x1, y1 = ternary_to_cartesian(0, t, 1-t)
        x2, y2 = ternary_to_cartesian(1-t, t, 0)
        ax.plot([x1, x2], [y1, y2], 'gray', linewidth=0.5, alpha=0.3)
        x1, y1 = ternary_to_cartesian(t, 0, 1-t)
        x2, y2 = ternary_to_cartesian(0, t, 1-t)
        ax.plot([x1, x2], [y1, y2], 'gray', linewidth=0.5, alpha=0.3)
    
    ax.text(0, -0.05, 'A', fontsize=12, ha='center', fontweight='bold')
    ax.text(1, -0.05, 'B', fontsize=12, ha='center', fontweight='bold')
    ax.text(0.5, np.sqrt(3)/2 + 0.05, 'C', fontsize=12, ha='center', fontweight='bold')

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 左图：颜色映射
ax1 = axes[0]
draw_ternary_base(ax1)

x_coords = [ternary_to_cartesian(a[i], b[i], c[i])[0] for i in range(n)]
y_coords = [ternary_to_cartesian(a[i], b[i], c[i])[1] for i in range(n)]

scatter1 = ax1.scatter(x_coords, y_coords, c=color_values, cmap='RdYlBu_r', 
                      s=100, alpha=0.8, edgecolors='white', linewidth=0.5)
cbar1 = plt.colorbar(scatter1, ax=ax1, shrink=0.6, pad=0.02)
cbar1.set_label('变量D值', fontsize=10)

ax1.set_xlim(-0.1, 1.1)
ax1.set_ylim(-0.1, 1.0)
ax1.set_aspect('equal')
ax1.axis('off')
ax1.set_title('颜色映射的三元相散点图', fontsize=12)

# 右图：散点大小映射
ax2 = axes[1]
draw_ternary_base(ax2)

scatter2 = ax2.scatter(x_coords, y_coords, s=size_values * 2, c='#4DBBD5', 
                      alpha=0.6, edgecolors='white', linewidth=1)

# 添加图例
sizes_legend = [50, 150, 300]
labels_legend = ['小', '中', '大']
for size, label in zip(sizes_legend, labels_legend):
    ax2.scatter([], [], s=size * 2, c='#4DBBD5', alpha=0.6, 
               edgecolors='white', label=label)
ax2.legend(title='大小', loc='upper right', frameon=True, fontsize=9)

ax2.set_xlim(-0.1, 1.1)
ax2.set_ylim(-0.1, 1.0)
ax2.set_aspect('equal')
ax2.axis('off')
ax2.set_title('散点大小映射的三元相散点图', fontsize=12)

plt.suptitle('颜色、散点大小映射的三元相散点图绘制示例', fontsize=14)
plt.tight_layout()
plt.show()
