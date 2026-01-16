# seaborn分组误差柱形图单独数据点绘制示例
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 数据加载：优先读取外部文件，否则使用内置数据
def load_data():
    for fname in ['示范数据.xlsx', '示范数据.csv']:
        if os.path.exists(fname):
            try:
                if fname.endswith('.csv'):
                    return pd.read_csv(fname)
                else:
                    return pd.read_excel(fname)
            except Exception:
                pass
    # 内置示例数据
    np.random.seed(42)
    n = 20
    return pd.DataFrame({
        '组别': np.repeat(['组A', '组B', '组C'], n),
        '类型': np.tile(np.repeat(['类型1', '类型2'], n//2), 3),
        '数值': np.concatenate([
            np.random.normal(50, 10, n),
            np.random.normal(60, 12, n),
            np.random.normal(55, 8, n),
        ])
    })

data = load_data()

# 创建图形
fig, ax = plt.subplots(figsize=(10, 7))

# 绘制分组柱形图（带误差线）
palette = ['#E64B35', '#4DBBD5']
bars = sns.barplot(data=data, x='组别', y='数值', hue='类型', 
                  palette=palette, ax=ax, errorbar='sd', capsize=0.1,
                  edgecolor='white', linewidth=1)

# 添加单独数据点
sns.stripplot(data=data, x='组别', y='数值', hue='类型',
             palette=['#333333', '#666666'], dodge=True, 
             alpha=0.5, size=5, ax=ax, legend=False)

ax.set_xlabel('组别', fontsize=12)
ax.set_ylabel('数值', fontsize=12)
ax.set_title('分组误差柱形图（带数据点）', fontsize=14)
ax.legend(title='类型', loc='upper right', frameon=True)
ax.grid(True, linestyle='--', alpha=0.3, axis='y')

plt.tight_layout()
plt.show()
