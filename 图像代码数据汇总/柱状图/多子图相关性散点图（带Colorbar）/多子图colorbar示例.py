# 20250705新加 - 多子图相关性散点图添加colorbar绘制示例（位置属性为right）
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from mpl_toolkits.axes_grid1 import make_axes_locatable

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 创建示例数据
np.random.seed(42)
n = 100

# 不同变量组合
combinations = [
    ('X1', 'Y1'), ('X2', 'Y2'), 
    ('X3', 'Y3'), ('X4', 'Y4')
]

# 创建图形
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

for ax, (x_name, y_name) in zip(axes.flat, combinations):
    # 生成数据
    x = np.random.uniform(0, 10, n)
    y = x + np.random.normal(0, 2, n)
    z = np.random.uniform(0, 100, n)  # 用于颜色映射的第三变量
    
    # 绘制散点图
    scatter = ax.scatter(x, y, c=z, cmap='viridis', s=60, alpha=0.7, 
                        edgecolors='white', linewidth=0.5)
    
    # 添加回归线
    z_fit = np.polyfit(x, y, 1)
    p = np.poly1d(z_fit)
    x_line = np.linspace(x.min(), x.max(), 100)
    ax.plot(x_line, p(x_line), 'r--', linewidth=2, label='回归线')
    
    # 计算相关系数
    corr = np.corrcoef(x, y)[0, 1]
    
    # 添加colorbar到右侧
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.1)
    cbar = plt.colorbar(scatter, cax=cax)
    cbar.set_label('Z值', fontsize=10)
    
    # 添加统计信息
    ax.text(0.05, 0.95, f'r = {corr:.3f}', transform=ax.transAxes, fontsize=11,
           verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.set_xlabel(x_name, fontsize=11)
    ax.set_ylabel(y_name, fontsize=11)
    ax.set_title(f'{x_name} vs {y_name} 相关性散点图', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.3)
    ax.legend(loc='lower right')

plt.suptitle('多子图相关性散点图添加colorbar示例（位置属性为right）', fontsize=14)
plt.tight_layout()
plt.show()
