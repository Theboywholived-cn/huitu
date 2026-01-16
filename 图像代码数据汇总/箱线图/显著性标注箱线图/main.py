# 带显著性标注箱线图绘制示例
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

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
    n = 30
    return pd.DataFrame({
        '组别': np.repeat(['对照组', '实验组A', '实验组B', '实验组C'], n),
        '数值': np.concatenate([
            np.random.normal(50, 8, n),
            np.random.normal(60, 10, n),
            np.random.normal(55, 7, n),
            np.random.normal(70, 9, n),
        ])
    })

data = load_data()

# 创建图形
fig, ax = plt.subplots(figsize=(10, 7))

# 绘制箱线图
palette = ['#E64B35', '#4DBBD5', '#00A087', '#F39B7F']
box = sns.boxplot(data=data, x='组别', y='数值', palette=palette, ax=ax,
                 width=0.6, linewidth=1.5)

# 添加数据点
sns.stripplot(data=data, x='组别', y='数值', color='black', 
             alpha=0.4, size=4, ax=ax)

# 计算显著性并添加标注
groups = data['组别'].unique()
y_max = data['数值'].max()
h = 3  # 标注线高度

def add_significance(x1, x2, y, p_val):
    """添加显著性标注"""
    if p_val < 0.001:
        sig = '***'
    elif p_val < 0.01:
        sig = '**'
    elif p_val < 0.05:
        sig = '*'
    else:
        sig = 'ns'
    
    ax.plot([x1, x1, x2, x2], [y, y+h, y+h, y], 'k-', linewidth=1)
    ax.text((x1+x2)/2, y+h, sig, ha='center', va='bottom', fontsize=12)

# 比较对照组和各实验组
control = data[data['组别'] == '对照组']['数值']
for i, group in enumerate(['实验组A', '实验组B', '实验组C']):
    exp_data = data[data['组别'] == group]['数值']
    _, p_val = stats.ttest_ind(control, exp_data)
    add_significance(0, i+1, y_max + 5 + i*8, p_val)

ax.set_xlabel('组别', fontsize=12)
ax.set_ylabel('数值', fontsize=12)
ax.set_title('带显著性标注的箱线图\n(*: p<0.05, **: p<0.01, ***: p<0.001, ns: 不显著)', fontsize=13)
ax.grid(True, linestyle='--', alpha=0.3, axis='y')

plt.tight_layout()
plt.show()
