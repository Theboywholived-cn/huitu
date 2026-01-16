# 多子图相关性散点图添加colorbar绘制示例
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
import matplotlib.cm as cm
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
                if 'X' in df.columns and 'Y' in df.columns:
                    data_sets = []
                    group_col = None
                    for col in ['组别', 'Group', '子图']:
                        if col in df.columns:
                            group_col = col
                            break
                    z_col = 'Z' if 'Z' in df.columns else None
                    if group_col:
                        for g in sorted(df[group_col].unique()):
                            sub = df[df[group_col] == g]
                            x = sub['X'].values
                            y = sub['Y'].values
                            z = sub['Z'].values if z_col else np.abs(x * y) + np.random.rand(len(x)) * 10
                            data_sets.append((x, y, z))
                    else:
                        x, y = df['X'].values, df['Y'].values
                        z = df['Z'].values if z_col else np.abs(x * y) + np.random.rand(len(x)) * 10
                        data_sets.append((x, y, z))
                    return data_sets
            except Exception:
                pass
    # 内置示例数据
    np.random.seed(42)
    n = 100
    data_sets = []
    for i in range(4):
        x = np.random.randn(n) * (i + 1)
        y = x * (0.5 + i * 0.2) + np.random.randn(n) * 2
        z = np.abs(x * y) + np.random.rand(n) * 10
        data_sets.append((x, y, z))
    return data_sets

# 加载数据
data_sets = load_data()

# 创建图形
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

# 统一颜色范围
all_z = np.concatenate([d[2] for d in data_sets])
vmin, vmax = all_z.min(), all_z.max()
norm = Normalize(vmin=vmin, vmax=vmax)
cmap = cm.viridis

titles = ['组 A', '组 B', '组 C', '组 D']

for idx, (ax, (x, y, z)) in enumerate(zip(axes, data_sets)):
    sc = ax.scatter(x, y, c=z, cmap=cmap, norm=norm, s=50, alpha=0.7, edgecolors='white', linewidth=0.5)
    ax.set_xlabel('X 变量', fontsize=11)
    ax.set_ylabel('Y 变量', fontsize=11)
    ax.set_title(titles[idx], fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.3)
    
    # 添加回归线
    z_fit = np.polyfit(x, y, 1)
    p = np.poly1d(z_fit)
    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, p(x_line), 'r--', linewidth=2, alpha=0.8)
    
    # 计算R²
    r2 = np.corrcoef(x, y)[0, 1] ** 2
    ax.text(0.05, 0.95, f'R² = {r2:.3f}', transform=ax.transAxes, 
            fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

# 添加右侧colorbar
fig.subplots_adjust(right=0.85)
cbar_ax = fig.add_axes([0.88, 0.15, 0.03, 0.7])
cbar = fig.colorbar(cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax)
cbar.set_label('数值强度', fontsize=11)

plt.suptitle('多子图相关性散点图（带Colorbar）', fontsize=14, y=0.98)
plt.tight_layout(rect=[0, 0, 0.85, 0.95])
plt.show()
