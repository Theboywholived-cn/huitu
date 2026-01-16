# 百分比堆积柱形图绘制
import numpy as np
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 创建示例数据
categories = ['类别A', '类别B', '类别C', '类别D', '类别E']
data1 = np.array([25, 32, 28, 35, 30])
data2 = np.array([18, 22, 25, 18, 28])
data3 = np.array([30, 25, 22, 28, 20])
data4 = np.array([27, 21, 25, 19, 22])

# 计算百分比
total = data1 + data2 + data3 + data4
pct1 = data1 / total * 100
pct2 = data2 / total * 100
pct3 = data3 / total * 100
pct4 = data4 / total * 100

# 创建图形
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# 左图：垂直百分比堆积柱形图
ax1 = axes[0]
x = np.arange(len(categories))
width = 0.6
colors = ['#E64B35', '#4DBBD5', '#00A087', '#3C5488']

bars1 = ax1.bar(x, pct1, width, label='系列1', color=colors[0], edgecolor='white')
bars2 = ax1.bar(x, pct2, width, bottom=pct1, label='系列2', color=colors[1], edgecolor='white')
bars3 = ax1.bar(x, pct3, width, bottom=pct1+pct2, label='系列3', color=colors[2], edgecolor='white')
bars4 = ax1.bar(x, pct4, width, bottom=pct1+pct2+pct3, label='系列4', color=colors[3], edgecolor='white')

# 添加百分比标签
for i in range(len(categories)):
    ax1.text(x[i], pct1[i]/2, f'{pct1[i]:.1f}%', ha='center', va='center', fontsize=9, color='white')
    ax1.text(x[i], pct1[i] + pct2[i]/2, f'{pct2[i]:.1f}%', ha='center', va='center', fontsize=9, color='white')
    ax1.text(x[i], pct1[i] + pct2[i] + pct3[i]/2, f'{pct3[i]:.1f}%', ha='center', va='center', fontsize=9, color='white')
    ax1.text(x[i], pct1[i] + pct2[i] + pct3[i] + pct4[i]/2, f'{pct4[i]:.1f}%', ha='center', va='center', fontsize=9, color='white')

ax1.set_xlabel('类别', fontsize=11)
ax1.set_ylabel('百分比 (%)', fontsize=11)
ax1.set_title('垂直百分比堆积柱形图', fontsize=12)
ax1.set_xticks(x)
ax1.set_xticklabels(categories)
ax1.set_ylim(0, 100)
ax1.legend(loc='upper right', frameon=True)
ax1.grid(True, axis='y', linestyle='--', alpha=0.3)

# 右图：水平百分比堆积柱形图
ax2 = axes[1]
y = np.arange(len(categories))
height = 0.6

bars1_h = ax2.barh(y, pct1, height, label='系列1', color=colors[0], edgecolor='white')
bars2_h = ax2.barh(y, pct2, height, left=pct1, label='系列2', color=colors[1], edgecolor='white')
bars3_h = ax2.barh(y, pct3, height, left=pct1+pct2, label='系列3', color=colors[2], edgecolor='white')
bars4_h = ax2.barh(y, pct4, height, left=pct1+pct2+pct3, label='系列4', color=colors[3], edgecolor='white')

# 添加百分比标签
for i in range(len(categories)):
    ax2.text(pct1[i]/2, y[i], f'{pct1[i]:.1f}%', ha='center', va='center', fontsize=9, color='white')
    ax2.text(pct1[i] + pct2[i]/2, y[i], f'{pct2[i]:.1f}%', ha='center', va='center', fontsize=9, color='white')
    ax2.text(pct1[i] + pct2[i] + pct3[i]/2, y[i], f'{pct3[i]:.1f}%', ha='center', va='center', fontsize=9, color='white')
    ax2.text(pct1[i] + pct2[i] + pct3[i] + pct4[i]/2, y[i], f'{pct4[i]:.1f}%', ha='center', va='center', fontsize=9, color='white')

ax2.set_xlabel('百分比 (%)', fontsize=11)
ax2.set_ylabel('类别', fontsize=11)
ax2.set_title('水平百分比堆积柱形图', fontsize=12)
ax2.set_yticks(y)
ax2.set_yticklabels(categories)
ax2.set_xlim(0, 100)
ax2.legend(loc='lower right', frameon=True)
ax2.grid(True, axis='x', linestyle='--', alpha=0.3)

plt.suptitle('百分比堆积柱形图绘制示例', fontsize=14)
plt.tight_layout()
plt.show()
