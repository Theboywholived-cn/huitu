import matplotlib
matplotlib.use('Agg') # 必须在 backend 运行
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import os

# 1. 自动寶找目录下的数据文件（优先 CSV，其次 Excel）
data_file = next((f for f in os.listdir('.') if f.endswith(('.csv', '.xlsx', '.xls'))), None)
if not data_file:
    raise FileNotFoundError("未在当前目录找到数据文件")

# 2. 加载数据
df = pd.read_csv(data_file) if data_file.endswith('.csv') else pd.read_excel(data_file)

# 3. 绘图配置
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 假设前三列分别是 x, y, z
x = df.iloc[:, 0].values
y = df.iloc[:, 1].values
z = df.iloc[:, 2].values

# 4. 使用 plot_trisurf 绘制散点生成的曲面
# cmap 使用 viridis 或 coolwarm 增强立体感
surf = ax.plot_trisurf(x, y, z, cmap='viridis', edgecolor='none', antialiased=True)

# 5. 修饰
ax.set_xlabel(df.columns[0])
ax.set_ylabel(df.columns[1])
ax.set_zlabel(df.columns[2])
fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
plt.title('3D Surface Analysis')

# 6. 保存由后端捕获
plt.savefig('output.png', dpi=150, bbox_inches='tight')
