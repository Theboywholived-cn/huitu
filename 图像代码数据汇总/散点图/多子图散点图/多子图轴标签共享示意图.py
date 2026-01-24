# 胡涛 - 使用ProPlot绘制的多子图轴标签共享示意图
import numpy as np
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 创建数据
np.random.seed(42)
x = np.linspace(0, 10, 100)

# 创建共享轴标签的子图
fig, axes = plt.subplots(2, 3, figsize=(14, 8), 
                         sharex=True, sharey=True)

colors = ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4']
functions = [
    (np.sin(x), 'sin(x)'),
    (np.cos(x), 'cos(x)'),
    (np.sin(2*x), 'sin(2x)'),
    (np.cos(2*x), 'cos(2x)'),
    (np.sin(x) * np.exp(-x/10), '衰减sin(x)'),
    (np.cos(x) * np.exp(-x/10), '衰减cos(x)')
]

for ax, (y, title), color in zip(axes.flat, functions, colors):
    ax.plot(x, y, color=color, linewidth=2)
    ax.fill_between(x, y, alpha=0.2, color=color)
    ax.set_title(title, fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)

# 只在边缘子图添加轴标签（模拟共享效果）
for ax in axes[-1, :]:
    ax.set_xlabel('X', fontsize=12)
for ax in axes[:, 0]:
    ax.set_ylabel('Y', fontsize=12)

plt.suptitle('多子图轴标签共享示意图', fontsize=14)
plt.tight_layout()
plt.show()
