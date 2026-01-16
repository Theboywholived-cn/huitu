# 矩阵气泡图绘制示例
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
                # 矩阵形式的数据
                if len(df.columns) >= 2:
                    rows = df.iloc[:, 0].tolist()
                    cols = df.columns[1:].tolist()
                    values = df.iloc[:, 1:].values.astype(float)
                    sizes = values / values.max() * 500 + 100
                    return rows, cols, values, sizes
            except Exception:
                pass
    # 内置示例数据
    np.random.seed(42)
    rows = ['行1', '行2', '行3', '行4', '行5']
    cols = ['列1', '列2', '列3', '列4', '列5', '列6']
    values = np.random.rand(len(rows), len(cols)) * 100
    sizes = np.random.rand(len(rows), len(cols)) * 500 + 100
    return rows, cols, values, sizes

# 加载数据
rows, cols, values, sizes = load_data()

# 创建图形
fig, ax = plt.subplots(figsize=(12, 8))

# 绘制气泡图
for i, row in enumerate(rows):
    for j, col in enumerate(cols):
        size = sizes[i, j]
        color_val = values[i, j]
        scatter = ax.scatter(j, i, s=size, c=[color_val], cmap='RdYlBu_r', 
                           vmin=0, vmax=100, alpha=0.7, edgecolors='white', linewidth=1)

# 添加颜色条
cbar = plt.colorbar(scatter, ax=ax, shrink=0.8)
cbar.set_label('数值大小', fontsize=11)

# 设置坐标轴
ax.set_xticks(range(len(cols)))
ax.set_xticklabels(cols, fontsize=11)
ax.set_yticks(range(len(rows)))
ax.set_yticklabels(rows, fontsize=11)

ax.set_xlabel('列变量', fontsize=12)
ax.set_ylabel('行变量', fontsize=12)
ax.set_title('矩阵气泡图', fontsize=14)

# 添加网格
ax.set_xlim(-0.5, len(cols) - 0.5)
ax.set_ylim(-0.5, len(rows) - 0.5)
ax.grid(True, linestyle='--', alpha=0.3)

# 添加图例说明气泡大小
for size, label in [(200, '小'), (400, '中'), (600, '大')]:
    ax.scatter([], [], s=size, c='gray', alpha=0.5, label=f'{label}')
ax.legend(title='气泡大小', loc='upper right', bbox_to_anchor=(1.25, 1))

plt.tight_layout()
plt.show()
