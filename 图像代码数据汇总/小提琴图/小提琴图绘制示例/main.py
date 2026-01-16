# 小提琴图绘制示例
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
    n = 50
    return pd.DataFrame({
        '组别': np.repeat(['组A', '组B', '组C', '组D'], n),
        '数值': np.concatenate([
            np.random.normal(50, 10, n),
            np.random.normal(60, 15, n),
            np.concatenate([np.random.normal(40, 5, n//2), np.random.normal(70, 5, n//2)]),
            np.random.exponential(10, n) + 30,
        ])
    })

data = load_data()

# 创建图形
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

palette = ['#E64B35', '#4DBBD5', '#00A087', '#F39B7F']

# 左上：基础小提琴图
ax1 = axes[0, 0]
sns.violinplot(data=data, x='组别', y='数值', palette=palette, ax=ax1)
ax1.set_title('基础小提琴图', fontsize=12)
ax1.grid(True, linestyle='--', alpha=0.3, axis='y')

# 右上：带箱线图的小提琴图
ax2 = axes[0, 1]
sns.violinplot(data=data, x='组别', y='数值', palette=palette, ax=ax2, inner='box')
ax2.set_title('小提琴图（内置箱线图）', fontsize=12)
ax2.grid(True, linestyle='--', alpha=0.3, axis='y')

# 左下：带数据点的小提琴图
ax3 = axes[1, 0]
sns.violinplot(data=data, x='组别', y='数值', palette=palette, ax=ax3, inner=None, alpha=0.7)
sns.stripplot(data=data, x='组别', y='数值', color='black', alpha=0.3, size=3, ax=ax3)
ax3.set_title('小提琴图（带数据点）', fontsize=12)
ax3.grid(True, linestyle='--', alpha=0.3, axis='y')

# 右下：分割小提琴图
ax4 = axes[1, 1]
data_split = data.copy()
data_split['性别'] = np.tile(['男', '女'], len(data)//2)
sns.violinplot(data=data_split, x='组别', y='数值', hue='性别', 
              palette=['#4DBBD5', '#E64B35'], split=True, ax=ax4)
ax4.set_title('分割小提琴图', fontsize=12)
ax4.legend(title='性别', loc='upper right')
ax4.grid(True, linestyle='--', alpha=0.3, axis='y')

plt.suptitle('小提琴图绘制示例', fontsize=14)
plt.tight_layout()
plt.show()
