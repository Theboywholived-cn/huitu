# 模型预测对比图绘制示例
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 数据加载：优先读取外部文件，否则使用内置数据
def load_data():
    for fname in ['示范数据.xlsx', '示范数据.csv']:
        if os.path.exists(fname):
            try:
                if fname.endswith('.csv'):
                    df = pd.read_csv(fname)
                else:
                    df = pd.read_excel(fname)
                # 查找实测值和预测值列
                cols = df.columns.tolist()
                actual_col = next((c for c in cols if '实测' in c or 'actual' in c.lower()), None)
                pred_col = next((c for c in cols if '预测' in c or 'pred' in c.lower()), None)
                if actual_col and pred_col:
                    return df[actual_col].values, df[pred_col].values
            except Exception:
                pass
    # 内置示例数据
    np.random.seed(42)
    n = 200
    x = np.arange(n)
    true_values = np.sin(x * 0.1) * 20 + 50 + np.random.normal(0, 2, n)
    pred_values = true_values + np.random.normal(0, 3, n)
    return true_values, pred_values

true_values, pred_values = load_data()
n = len(true_values)
x = np.arange(n)

# 创建图形
fig, axes = plt.subplots(2, 1, figsize=(12, 8))

# 上图：时间序列对比
ax1 = axes[0]
ax1.plot(x, true_values, 'b-', linewidth=1.5, label='实测值', alpha=0.8)
ax1.plot(x, pred_values, 'r--', linewidth=1.5, label='预测值', alpha=0.8)
ax1.fill_between(x, true_values, pred_values, alpha=0.2, color='gray')
ax1.set_xlabel('时间步', fontsize=11)
ax1.set_ylabel('数值', fontsize=11)
ax1.set_title('模型预测值与实测值对比', fontsize=12)
ax1.legend(loc='upper right', frameon=True)
ax1.grid(True, linestyle='--', alpha=0.3)

# 下图：散点图
ax2 = axes[1]
ax2.scatter(true_values, pred_values, c='#4DBBD5', alpha=0.6, s=30, edgecolors='white')
ax2.plot([min(true_values), max(true_values)], [min(true_values), max(true_values)], 
         'k--', linewidth=1.5, label='y=x')

# 计算指标
r2 = 1 - np.sum((true_values - pred_values)**2) / np.sum((true_values - np.mean(true_values))**2)
rmse = np.sqrt(np.mean((true_values - pred_values)**2))
mae = np.mean(np.abs(true_values - pred_values))

ax2.set_xlabel('实测值', fontsize=11)
ax2.set_ylabel('预测值', fontsize=11)
ax2.set_title(f'预测散点图 | R² = {r2:.4f}, RMSE = {rmse:.2f}, MAE = {mae:.2f}', fontsize=12)
ax2.legend(loc='upper left')
ax2.grid(True, linestyle='--', alpha=0.3)

plt.tight_layout()
plt.show()
