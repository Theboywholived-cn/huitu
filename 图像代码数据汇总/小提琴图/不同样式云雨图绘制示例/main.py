# 不同样式云雨图绘制示例
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
                    df = pd.read_csv(fname)
                else:
                    df = pd.read_excel(fname)
                # 转换为分组数据列表
                if '组别' in df.columns and '数值' in df.columns:
                    groups = df['组别'].unique()
                    return [df[df['组别'] == g]['数值'].values for g in groups], list(groups)
            except Exception:
                pass
    # 内置示例数据
    np.random.seed(42)
    categories = ['组A', '组B', '组C', '组D']
    data = [np.random.normal(loc, 0.5, 100) for loc in [2, 3.5, 2.8, 4]]
    return data, categories

data, categories = load_data()

# 创建图形
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# 样式1：半小提琴图 + 散点
ax1 = axes[0, 0]
parts = ax1.violinplot(data, positions=range(1, 5), showmeans=False, showmedians=False, showextrema=False)
for i, pc in enumerate(parts['bodies']):
    pc.set_facecolor(['#E64B35', '#4DBBD5', '#00A087', '#3C5488'][i])
    pc.set_alpha(0.6)
    # 只显示半边
    m = np.mean(pc.get_paths()[0].vertices[:, 0])
    pc.get_paths()[0].vertices[:, 0] = np.clip(pc.get_paths()[0].vertices[:, 0], -np.inf, m)

for i, d in enumerate(data):
    x = np.random.normal(i + 1.15, 0.04, len(d))
    ax1.scatter(x, d, alpha=0.5, s=20, c=['#E64B35', '#4DBBD5', '#00A087', '#3C5488'][i])

ax1.set_xticks(range(1, 5))
ax1.set_xticklabels(categories)
ax1.set_ylabel('值', fontsize=11)
ax1.set_title('样式1：半小提琴图 + 散点', fontsize=12)
ax1.grid(True, axis='y', linestyle='--', alpha=0.3)

# 样式2：小提琴图 + 箱线图
ax2 = axes[0, 1]
parts2 = ax2.violinplot(data, positions=range(1, 5), showmeans=False, showmedians=False, showextrema=False)
for i, pc in enumerate(parts2['bodies']):
    pc.set_facecolor(['#E64B35', '#4DBBD5', '#00A087', '#3C5488'][i])
    pc.set_alpha(0.4)
    
bp = ax2.boxplot(data, positions=range(1, 5), widths=0.15, 
                patch_artist=True, showfliers=False)
for i, patch in enumerate(bp['boxes']):
    patch.set_facecolor(['#E64B35', '#4DBBD5', '#00A087', '#3C5488'][i])
    patch.set_alpha(0.8)

ax2.set_xticks(range(1, 5))
ax2.set_xticklabels(categories)
ax2.set_ylabel('值', fontsize=11)
ax2.set_title('样式2：小提琴图 + 箱线图', fontsize=12)
ax2.grid(True, axis='y', linestyle='--', alpha=0.3)

# 样式3：云雨图（小提琴 + 散点 + 箱线）
ax3 = axes[1, 0]
parts3 = ax3.violinplot(data, positions=range(1, 5), showmeans=False, showmedians=False, showextrema=False)
for i, pc in enumerate(parts3['bodies']):
    pc.set_facecolor(['#E64B35', '#4DBBD5', '#00A087', '#3C5488'][i])
    pc.set_alpha(0.4)
    m = np.mean(pc.get_paths()[0].vertices[:, 0])
    pc.get_paths()[0].vertices[:, 0] = np.clip(pc.get_paths()[0].vertices[:, 0], -np.inf, m)

for i, d in enumerate(data):
    x = np.random.normal(i + 1.15, 0.04, len(d))
    ax3.scatter(x, d, alpha=0.4, s=15, c=['#E64B35', '#4DBBD5', '#00A087', '#3C5488'][i])

bp3 = ax3.boxplot(data, positions=[0.85, 1.85, 2.85, 3.85], widths=0.1, 
                 patch_artist=True, showfliers=False)
for i, patch in enumerate(bp3['boxes']):
    patch.set_facecolor(['#E64B35', '#4DBBD5', '#00A087', '#3C5488'][i])

ax3.set_xticks(range(1, 5))
ax3.set_xticklabels(categories)
ax3.set_ylabel('值', fontsize=11)
ax3.set_title('样式3：云雨图', fontsize=12)
ax3.grid(True, axis='y', linestyle='--', alpha=0.3)

# 样式4：带均值和误差棒
ax4 = axes[1, 1]
parts4 = ax4.violinplot(data, positions=range(1, 5), showmeans=False, showmedians=False, showextrema=False)
for i, pc in enumerate(parts4['bodies']):
    pc.set_facecolor(['#E64B35', '#4DBBD5', '#00A087', '#3C5488'][i])
    pc.set_alpha(0.5)

means = [np.mean(d) for d in data]
stds = [np.std(d) for d in data]
ax4.errorbar(range(1, 5), means, yerr=stds, fmt='o', capsize=5, capthick=2, 
            color='black', markersize=8, markerfacecolor='white', markeredgewidth=2)

ax4.set_xticks(range(1, 5))
ax4.set_xticklabels(categories)
ax4.set_ylabel('值', fontsize=11)
ax4.set_title('样式4：小提琴图 + 均值±标准差', fontsize=12)
ax4.grid(True, axis='y', linestyle='--', alpha=0.3)

plt.suptitle('不同样式云雨图绘制示例', fontsize=14)
plt.tight_layout()
plt.show()
