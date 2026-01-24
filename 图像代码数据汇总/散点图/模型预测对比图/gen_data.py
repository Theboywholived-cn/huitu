import pandas as pd
import numpy as np

np.random.seed(42)

# 生成模型预测对比图的示范数据
# 模拟地质测井数据：深度 vs 黏土含量

n = 400  # 数据点数量

# 深度列 (1600-2000米)
depth = np.linspace(1600, 2000, n)

# 真实黏土含量 (模拟复杂的地质变化)
base = 35 + 5 * np.sin(depth * 0.02) + 3 * np.cos(depth * 0.05)
noise = np.random.normal(0, 2, n)
true_values = base + noise

# 不同模型的预测结果
models = {
    'XGBoost': true_values + np.random.normal(0, 2.1, n),
    'FCN': true_values + np.random.normal(0, 1.8, n) + 0.5 * np.sin(depth * 0.01),
    'LSTM': true_values + np.random.normal(0, 1.6, n),
    'CNN-LSTM': true_values + np.random.normal(0, 1.2, n),
    'MLR': true_values + np.random.normal(0, 3.2, n) + 2 * np.sin(depth * 0.008),
}

# 创建数据框
data = {'Depth': depth, 'True': true_values}
for model_name, pred in models.items():
    data[model_name] = pred

df = pd.DataFrame(data)

# 保存数据
df.to_excel('模型预测数据.xlsx', index=False)
print('模型预测数据.xlsx 已生成')
print(f'数据形状: {df.shape}')
print(df.head(10))
print('\n列名:', df.columns.tolist())
