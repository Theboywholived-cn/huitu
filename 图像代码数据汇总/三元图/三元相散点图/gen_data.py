import pandas as pd
import numpy as np

np.random.seed(42)

# 生成三元图示范数据
n = 50  # 每组50个点

# 生成归一化的三元坐标 (三个变量和为1)
def generate_ternary_points(n, seed_offset=0):
    np.random.seed(42 + seed_offset)
    # 使用Dirichlet分布生成归一化的三元数据
    points = np.random.dirichlet([2, 2, 2], n)
    return points[:, 0], points[:, 1], points[:, 2]

# 生成两组数据 (Test 01 和 Test 02)
v1_1, v2_1, v3_1 = generate_ternary_points(n, 0)
v1_2, v2_2, v3_2 = generate_ternary_points(n, 100)

# 合并数据
df = pd.DataFrame({
    'Variable1': np.concatenate([v1_1, v1_2]),
    'Variable2': np.concatenate([v2_1, v2_2]),
    'Variable3': np.concatenate([v3_1, v3_2]),
    'Type': ['Test 01'] * n + ['Test 02'] * n,
    'Size Value': np.random.rand(2 * n)  # 用于颜色映射模式
})

# 保存数据
df.to_excel('三元图数据.xlsx', index=False)
print('三元图数据.xlsx 已生成')
print(f'数据形状: {df.shape}')
print(df.head(10))
print('\n数据统计:')
print(df.describe())
