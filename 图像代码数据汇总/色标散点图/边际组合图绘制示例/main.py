# 赵肸 - seaborn不同样式边际组合图绘制示例
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

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
                # 标准化列名
                df.columns = [c.lower() for c in df.columns]
                if 'x' in df.columns and 'y' in df.columns:
                    return df
            except Exception:
                pass
    # 内置示例数据
    np.random.seed(42)
    n = 200
    x = np.random.normal(0, 1, n)
    y = 0.8 * x + np.random.normal(0, 0.5, n)
    category = np.random.choice(['A', 'B'], n)
    return pd.DataFrame({'x': x, 'y': y, 'category': category})

df = load_data()

# 创建图形
fig = plt.figure(figsize=(16, 12))

# 样式1：散点图 + 直方图
ax1 = fig.add_subplot(2, 2, 1)
g1 = sns.jointplot(data=df, x='x', y='y', kind='scatter', 
                  color='#4DBBD5', alpha=0.6, height=5)
g1.figure.suptitle('样式1：散点图 + 直方图', y=1.02)
plt.close(g1.figure)

# 重新在子图中绘制
ax1_main = fig.add_axes([0.05, 0.55, 0.35, 0.35])
ax1_histx = fig.add_axes([0.05, 0.91, 0.35, 0.08], sharex=ax1_main)
ax1_histy = fig.add_axes([0.41, 0.55, 0.08, 0.35], sharey=ax1_main)

ax1_main.scatter(df['x'], df['y'], c='#4DBBD5', alpha=0.6, s=30)
ax1_histx.hist(df['x'], bins=20, color='#4DBBD5', alpha=0.7, edgecolor='white')
ax1_histy.hist(df['y'], bins=20, color='#4DBBD5', alpha=0.7, edgecolor='white', orientation='horizontal')

ax1_histx.set_title('样式1：散点图 + 直方图', fontsize=11)
ax1_histx.tick_params(labelbottom=False)
ax1_histy.tick_params(labelleft=False)
ax1_main.set_xlabel('X', fontsize=10)
ax1_main.set_ylabel('Y', fontsize=10)

# 样式2：六边形图 + 直方图
ax2_main = fig.add_axes([0.55, 0.55, 0.35, 0.35])
ax2_histx = fig.add_axes([0.55, 0.91, 0.35, 0.08], sharex=ax2_main)
ax2_histy = fig.add_axes([0.91, 0.55, 0.08, 0.35], sharey=ax2_main)

hb = ax2_main.hexbin(df['x'], df['y'], gridsize=15, cmap='YlOrRd', mincnt=1)
ax2_histx.hist(df['x'], bins=20, color='#E64B35', alpha=0.7, edgecolor='white')
ax2_histy.hist(df['y'], bins=20, color='#E64B35', alpha=0.7, edgecolor='white', orientation='horizontal')

ax2_histx.set_title('样式2：六边形图 + 直方图', fontsize=11)
ax2_histx.tick_params(labelbottom=False)
ax2_histy.tick_params(labelleft=False)
ax2_main.set_xlabel('X', fontsize=10)
ax2_main.set_ylabel('Y', fontsize=10)

# 样式3：散点图 + KDE
ax3_main = fig.add_axes([0.05, 0.05, 0.35, 0.35])
ax3_kdex = fig.add_axes([0.05, 0.41, 0.35, 0.08], sharex=ax3_main)
ax3_kdey = fig.add_axes([0.41, 0.05, 0.08, 0.35], sharey=ax3_main)

ax3_main.scatter(df['x'], df['y'], c='#00A087', alpha=0.6, s=30)
sns.kdeplot(data=df, x='x', ax=ax3_kdex, color='#00A087', fill=True, alpha=0.5)
sns.kdeplot(data=df, y='y', ax=ax3_kdey, color='#00A087', fill=True, alpha=0.5)

ax3_kdex.set_title('样式3：散点图 + KDE', fontsize=11)
ax3_kdex.tick_params(labelbottom=False)
ax3_kdey.tick_params(labelleft=False)
ax3_main.set_xlabel('X', fontsize=10)
ax3_main.set_ylabel('Y', fontsize=10)

# 样式4：分类散点图 + KDE
ax4_main = fig.add_axes([0.55, 0.05, 0.35, 0.35])
ax4_kdex = fig.add_axes([0.55, 0.41, 0.35, 0.08], sharex=ax4_main)
ax4_kdey = fig.add_axes([0.91, 0.05, 0.08, 0.35], sharey=ax4_main)

colors = {'A': '#3C5488', 'B': '#F39B7F'}
for cat, color in colors.items():
    mask = df['category'] == cat
    ax4_main.scatter(df.loc[mask, 'x'], df.loc[mask, 'y'], c=color, alpha=0.6, s=30, label=cat)
    sns.kdeplot(data=df[mask], x='x', ax=ax4_kdex, color=color, fill=True, alpha=0.3)
    sns.kdeplot(data=df[mask], y='y', ax=ax4_kdey, color=color, fill=True, alpha=0.3)

ax4_main.legend(loc='lower right')
ax4_kdex.set_title('样式4：分类散点图 + KDE', fontsize=11)
ax4_kdex.tick_params(labelbottom=False)
ax4_kdey.tick_params(labelleft=False)
ax4_main.set_xlabel('X', fontsize=10)
ax4_main.set_ylabel('Y', fontsize=10)

plt.show()
