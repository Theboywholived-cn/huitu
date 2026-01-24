import pandas as pd
import numpy as np

np.random.seed(42)

# 生成散点图示范数据
n = 100

# X轴数据
x = np.linspace(0, 10, n)

# 多个Y轴数据系列（带噪声）
y1 = 2 * x + 1 + np.random.normal(0, 1.5, n)
y2 = 1.5 * x + 3 + np.random.normal(0, 1.2, n)
y3 = x ** 1.5 + np.random.normal(0, 2, n)

# 分组列
groups = np.random.choice(['A组', 'B组', 'C组'], n)

df = pd.DataFrame({
    'X': x,
    'Y1': y1,
    'Y2': y2,
    'Y3': y3,
    '分组': groups
})

df.to_excel('散点图数据.xlsx', index=False)
print('散点图数据.xlsx 已生成')
print(f'数据形状: {df.shape}')
print(df.head())
