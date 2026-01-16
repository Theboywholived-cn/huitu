# 多数据组三元相散点图和类别三元相散点图绘制示例
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
                    groups = {}
                    if 'Group' in df.columns or '组别' in df.columns:
                        grp_col = 'Group' if 'Group' in df.columns else '组别'
                        for g in df[grp_col].unique():
                            sub = df[df[grp_col] == g]
                            groups[g] = (sub['A'].values, sub['B'].values, sub['C'].values)
                    else:
                        groups['数据'] = (df['A'].values, df['B'].values, df['C'].values)
                    return groups
            except Exception:
                pass
    # 内置示例数据
    np.random.seed(42)
    groups = {}
    for i, name in enumerate(['数据组1', '数据组2', '数据组3']):
        n = 25
        a = np.random.beta(3 + i, 2, n)
        b = np.random.beta(2, 3 + i, n)
        c = np.random.beta(2, 2, n)
        total = a + b + c
        groups[name] = (a/total, b/total, c/total)
    return groups

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

# 加载数据
data_groups = load_data()

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 左图：多数据组三元相散点图
ax1 = axes[0]
draw_ternary_base(ax1)

colors = ['#E64B35', '#4DBBD5', '#00A087', '#F39B7F', '#3C5488']
markers = ['o', 's', '^', 'D', 'v']

for i, (group_name, (a, b, c)) in enumerate(data_groups.items()):
    color = colors[i % len(colors)]
    marker = markers[i % len(markers)]
    n = len(a)
    
    x_coords = [ternary_to_cartesian(a[j], b[j], c[j])[0] for j in range(n)]
    y_coords = [ternary_to_cartesian(a[j], b[j], c[j])[1] for j in range(n)]
    
    ax1.scatter(x_coords, y_coords, c=color, marker=marker, s=80, 
               alpha=0.7, label=group_name, edgecolors='white', linewidth=0.5)

ax1.set_xlim(-0.1, 1.1)
ax1.set_ylim(-0.1, 1.0)
ax1.set_aspect('equal')
ax1.axis('off')
ax1.set_title('多数据组三元相散点图', fontsize=12)
ax1.legend(loc='upper right', frameon=True)

# 右图：类别三元相散点图
ax2 = axes[1]
draw_ternary_base(ax2)

categories = ['类别A', '类别B', '类别C', '类别D']
colors2 = ['#E64B35', '#4DBBD5', '#00A087', '#F39B7F']
centers = [(0.6, 0.2, 0.2), (0.2, 0.6, 0.2), (0.2, 0.2, 0.6), (0.33, 0.33, 0.34)]

for i, (cat, color, center) in enumerate(zip(categories, colors2, centers)):
    n = 20
    a = np.random.normal(center[0], 0.08, n)
    b = np.random.normal(center[1], 0.08, n)
    c = np.random.normal(center[2], 0.08, n)
    a, b, c = np.abs(a), np.abs(b), np.abs(c)
    total = a + b + c
    a, b, c = a/total, b/total, c/total
    
    x_coords = [ternary_to_cartesian(a[j], b[j], c[j])[0] for j in range(n)]
    y_coords = [ternary_to_cartesian(a[j], b[j], c[j])[1] for j in range(n)]
    
    ax2.scatter(x_coords, y_coords, c=color, marker='o', s=100, 
               alpha=0.7, label=cat, edgecolors='white', linewidth=1)

ax2.set_xlim(-0.1, 1.1)
ax2.set_ylim(-0.1, 1.0)
ax2.set_aspect('equal')
ax2.axis('off')
ax2.set_title('类别三元相散点图', fontsize=12)
ax2.legend(loc='upper right', frameon=True)

plt.suptitle('三元相散点图绘制示例', fontsize=14)
plt.tight_layout()
plt.show()
