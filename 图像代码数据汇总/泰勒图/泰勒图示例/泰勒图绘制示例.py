# 多模型评估指标泰勒图绘制示例
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.projections import PolarAxes
import mpl_toolkits.axisartist.floating_axes as FA
import mpl_toolkits.axisartist.grid_finder as GF

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def taylor_diagram(ax, ref_std, samples, colors, markers, labels):
    """绘制泰勒图"""
    # 相关系数弧线
    angles = np.linspace(0, np.pi/2, 100)
    for r in [0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 0.99]:
        x = ref_std * r * np.cos(np.arccos(r))
        y = ref_std * r * np.sin(np.arccos(r))
        ax.plot([0, ref_std * np.cos(np.arccos(r))], 
                [0, ref_std * np.sin(np.arccos(r))], 
                'k--', alpha=0.3, linewidth=0.5)
    
    # 绘制参考点
    ax.plot(ref_std, 0, 'ko', markersize=10, label='观测值')
    
    # 绘制各模型点
    for i, (std, corr) in enumerate(samples):
        theta = np.arccos(corr)
        ax.plot(std * np.cos(theta), std * np.sin(theta), 
               marker=markers[i], color=colors[i], markersize=10, 
               label=labels[i], markeredgecolor='white', markeredgewidth=1)
    
    return ax

# 模拟数据
np.random.seed(42)
ref_std = 1.0  # 参考标准差

# 各模型的标准差和相关系数
models_data = [
    (0.9, 0.95),   # XGBoost
    (1.1, 0.88),   # FCN
    (1.05, 0.92),  # LSTM
    (0.95, 0.96),  # CNN-LSTM
]

colors = ['#E64B35', '#4DBBD5', '#00A087', '#F39B7F']
markers = ['o', 's', '^', 'D']
labels = ['XGBoost', 'FCN', 'LSTM', 'CNN-LSTM']

# 创建图形
fig, ax = plt.subplots(figsize=(10, 8))

# 绘制泰勒图框架
max_std = 1.5
ax.set_xlim(0, max_std)
ax.set_ylim(0, max_std)

# 绘制标准差圆弧
for std in [0.5, 1.0, 1.5]:
    circle = plt.Circle((0, 0), std, fill=False, linestyle='--', alpha=0.3)
    ax.add_patch(circle)

# 绘制相关系数线
for corr in [0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 0.99]:
    angle = np.arccos(corr)
    ax.plot([0, max_std * np.cos(angle)], [0, max_std * np.sin(angle)], 
            'b--', alpha=0.3, linewidth=0.5)
    ax.text(max_std * np.cos(angle) * 1.05, max_std * np.sin(angle) * 1.05, 
            f'{corr}', fontsize=9, alpha=0.7)

# 绘制参考点和RMSD圆
ax.plot(ref_std, 0, 'ko', markersize=12, label='观测值', zorder=5)
for rmsd in [0.25, 0.5, 0.75, 1.0]:
    circle = plt.Circle((ref_std, 0), rmsd, fill=False, linestyle=':', color='green', alpha=0.5)
    ax.add_patch(circle)

# 绘制各模型点
for i, (std, corr) in enumerate(models_data):
    theta = np.arccos(corr)
    x = std * np.cos(theta)
    y = std * np.sin(theta)
    ax.plot(x, y, marker=markers[i], color=colors[i], markersize=12, 
           label=labels[i], markeredgecolor='white', markeredgewidth=1.5, zorder=5)

ax.set_xlabel('标准差', fontsize=12)
ax.set_ylabel('标准差', fontsize=12)
ax.set_title('多模型评估指标泰勒图', fontsize=14)
ax.legend(loc='upper right', frameon=True, fancybox=True)
ax.set_aspect('equal')
ax.grid(True, linestyle='--', alpha=0.3)

plt.tight_layout()
plt.show()
