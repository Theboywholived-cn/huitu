# XGBoost, FCN, LSTM, CNN_LSTM模型散点对比图
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# 数据加载：优先读取外部文件，否则使用内置数据
def load_data():
    for fname in ['示范数据.xlsx', '示范数据.csv']:
        if os.path.exists(fname):
            try:
                if fname.endswith('.csv'):
                    df = pd.read_csv(fname)
                else:
                    df = pd.read_excel(fname)
                # 查找实测值列
                cols = df.columns.tolist()
                actual_col = next((c for c in cols if '实测' in c), None)
                if actual_col:
                    true_vals = df[actual_col].values
                    models = {}
                    for c in cols:
                        if '预测' in c:
                            model_name = c.replace('预测值_', '').replace('预测_', '')
                            models[model_name] = df[c].values
                    if models:
                        return true_vals, models
            except Exception:
                pass
    # 内置示例数据
    np.random.seed(42)
    n = 100
    true_values = np.linspace(0, 100, n)
    models = {
        'XGBoost': true_values + np.random.normal(0, 5, n),
        'FCN': true_values + np.random.normal(2, 8, n),
        'LSTM': true_values + np.random.normal(-1, 6, n),
        'CNN-LSTM': true_values + np.random.normal(0.5, 4, n)
    }
    return true_values, models

true_values, models = load_data()

# 创建2x2子图
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

colors = ['#E64B35', '#4DBBD5', '#00A087', '#F39B7F']

for idx, (model_name, pred_values) in enumerate(models.items()):
    ax = axes[idx]
    
    # 绘制散点图
    ax.scatter(true_values, pred_values, c=colors[idx], alpha=0.6, s=30, edgecolors='white', linewidth=0.5)
    
    # 绘制理想线 y=x
    ax.plot([0, 100], [0, 100], 'k--', linewidth=1.5, label='理想线 (y=x)')
    
    # 计算R²
    ss_res = np.sum((true_values - pred_values) ** 2)
    ss_tot = np.sum((true_values - np.mean(true_values)) ** 2)
    r2 = 1 - (ss_res / ss_tot)
    
    # 计算RMSE
    rmse = np.sqrt(np.mean((true_values - pred_values) ** 2))
    
    ax.set_xlabel('实测值', fontsize=11)
    ax.set_ylabel('预测值', fontsize=11)
    ax.set_title(f'{model_name}\nR² = {r2:.4f}, RMSE = {rmse:.2f}', fontsize=12)
    ax.legend(loc='upper left', frameon=True)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)
    ax.set_aspect('equal')

plt.suptitle('多模型预测效果对比', fontsize=14, y=1.02)
plt.tight_layout()
plt.show()
