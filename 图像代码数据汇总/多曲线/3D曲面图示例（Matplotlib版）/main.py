import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import glob
import os

# 1. 智能读取数据（查找 csv 或 xlsx）
data_files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
if not data_files:
    raise ValueError("未找到数据文件！")
    
filename = data_files[0]
if filename.endswith('.csv'):
    df = pd.read_csv(filename)
else:
    df = pd.read_excel(filename)

print(f"正在使用数据文件: {filename}, 数据形状: {df.shape}")

# 2. 设置绘图
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 3. 核心逻辑：判断数据类型并绘图
# 情况 A: 数据已经是一个矩阵（Index是Y，Columns是X，Values是Z）
# 适用于：pivot 后的数据，或类似相关系数矩阵
if df.shape[0] > 1 and df.shape[1] > 3 and df.dtypes.apply(lambda x: np.issubdtype(x, np.number)).all():
    print("检测到矩阵格式数据，使用 plot_surface")
    X, Y = np.meshgrid(np.arange(df.shape[1]), np.arange(df.shape[0]))
    Z = df.values
    surf = ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='none')
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

# 情况 B: 数据是 3 列 (x, y, z) 形式
# 适用于：标准的测量数据、实验数据
elif df.shape[1] >= 3:
    print("检测到 XYZ 列表格式数据")
    # 假设前三列分别是 x, y, z
    x = df.iloc[:, 0].values
    y = df.iloc[:, 1].values
    z = df.iloc[:, 2].values
    
    # 尝试 1: 如果数据本身就是网格化排列的（例如 10x10 的网格拉平成了 100行）
    # 尝试重塑 (Reshape) - 需要猜测网格大小，比较困难，这里推荐用三角剖分
    
    # 尝试 2: 使用 plot_trisurf (三角剖分曲面)，这是最通用的方法
    print("使用 plot_trisurf 绘制非网格数据")
    surf = ax.plot_trisurf(x, y, z, cmap='viridis', edgecolor='none')
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)

else:
    raise ValueError("数据列数不足，无法绘制 3D 图。请提供至少 3 列数据 (x, y, z) 或 矩阵数据。")

ax.set_xlabel('X')
ax.set_ylabel('Y')
ax.set_zlabel('Z')
plt.title(f'3D Surface Plot ({filename})')

# 保存（后端会自动处理显示）
# 注意：backend/app/api/routes_templates.py 会自动捕获生成的 output.png
# 但为了保险，我们可以显式保存
plt.savefig('output.png', dpi=150, bbox_inches='tight')
