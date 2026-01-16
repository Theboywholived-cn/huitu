# 20250705新加 - 多模型评估指标不同样式泰勒图绘制示例
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.projections import PolarAxes
import mpl_toolkits.axisartist.floating_axes as FA
import mpl_toolkits.axisartist.grid_finder as GF
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    """加载外部数据或返回内置示例数据"""
    for fname in ['示范数据.xlsx', '示范数据.csv']:
        if os.path.exists(fname):
            try:
                df = pd.read_excel(fname) if fname.endswith('.xlsx') else pd.read_csv(fname)
                if '模型' in df.columns and '相关系数' in df.columns and '标准差' in df.columns:
                    models = []
                    colors = ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4', '#91D1C2', '#DC0000']
                    markers = ['o', 's', '^', 'D', 'v', 'p', 'h', '*']
                    for i, row in df.iterrows():
                        models.append((
                            row['模型'],
                            row['相关系数'],
                            row['标准差'],
                            colors[i % len(colors)],
                            markers[i % len(markers)]
                        ))
                    return models
            except Exception:
                pass
    # 内置示例数据
    return [
        ('XGBoost', 0.95, 1.05, '#E64B35', 'o'),
        ('FCN', 0.88, 1.15, '#4DBBD5', 's'),
        ('LSTM', 0.92, 0.95, '#00A087', '^'),
        ('CNN-LSTM', 0.97, 1.02, '#3C5488', 'D'),
        ('Random Forest', 0.85, 1.20, '#F39B7F', 'v'),
        ('SVR', 0.80, 1.30, '#8491B4', 'p')
    ]

# 加载数据
models = load_data()

def taylor_diagram(ax, ref_std, samples, labels, colors, markers):
    """
    绘制泰勒图
    ref_std: 参考数据的标准差
    samples: [(correlation, std), ...] 每个模型的相关系数和标准差
    """
    # 设置角度范围（相关系数从0到1对应0到90度）
    theta_max = np.pi / 2
    
    # 绘制参考点
    ax.plot(0, ref_std, 'ko', markersize=10, label='观测值')
    
    # 绘制标准差弧线
    theta_range = np.linspace(0, theta_max, 100)
    for std in [0.5, 1.0, 1.5, 2.0]:
        r = std * ref_std
        ax.plot(theta_range, np.full_like(theta_range, r), 'gray', alpha=0.3, linewidth=0.5)
    
    # 绘制相关系数径向线
    for corr in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]:
        theta = np.arccos(corr)
        ax.plot([theta, theta], [0, 2 * ref_std], 'gray', alpha=0.3, linewidth=0.5)
    
    # 绘制RMSE等值线（以参考点为圆心）
    for rmse in [0.5, 1.0, 1.5]:
        theta_rmse = np.linspace(0, theta_max, 100)
        r_rmse = np.sqrt(ref_std**2 + (rmse * ref_std)**2 - 2 * ref_std * (rmse * ref_std) * np.cos(theta_rmse))
        valid = r_rmse <= 2 * ref_std
        ax.plot(theta_rmse[valid], r_rmse[valid], 'g--', alpha=0.5, linewidth=0.5)
    
    # 绘制各模型点
    for (corr, std), label, color, marker in zip(samples, labels, colors, markers):
        theta = np.arccos(corr)
        r = std
        ax.plot(theta, r, marker=marker, color=color, markersize=12, 
               markeredgecolor='white', markeredgewidth=1.5, label=label)

# 创建图形
fig = plt.figure(figsize=(12, 10))

# 使用极坐标
ax = fig.add_subplot(111, projection='polar')
ax.set_theta_zero_location('N')
ax.set_theta_direction(-1)
ax.set_thetamin(0)
ax.set_thetamax(90)

# 设置参考标准差
ref_std = 1.0

# 绘制参考点
ax.plot(0, ref_std, 'ko', markersize=12, label='观测值', zorder=5)

# 绘制相关系数标签
for corr in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99]:
    theta = np.arccos(corr)
    ax.annotate(f'{corr}', xy=(theta, 2.1), fontsize=8, ha='center')

# 绘制各模型点
for name, corr, std, color, marker in models:
    theta = np.arccos(corr)
    ax.plot(theta, std, marker=marker, color=color, markersize=12, 
           markeredgecolor='white', markeredgewidth=1.5, label=name, zorder=4)

# 绘制标准差参考弧线
theta_range = np.linspace(0, np.pi/2, 100)
for std_val in [0.5, 1.0, 1.5, 2.0]:
    ax.plot(theta_range, np.full_like(theta_range, std_val), 'gray', 
           alpha=0.3, linewidth=0.5, linestyle='--')

# 绘制以参考点为圆心的RMSE圆弧
for rmse in [0.25, 0.5, 0.75, 1.0]:
    theta_circle = np.linspace(0, np.pi/2, 100)
    # RMSE圆弧：以(0, ref_std)为圆心
    r_circle = []
    valid_theta = []
    for t in theta_circle:
        # 使用余弦定理计算
        r = np.sqrt(ref_std**2 + rmse**2 - 2*ref_std*rmse*np.cos(np.pi/2 - t))
        if 0 <= r <= 2.2:
            r_circle.append(r)
            valid_theta.append(t)
    if len(r_circle) > 0:
        ax.plot(valid_theta, r_circle, 'g--', alpha=0.4, linewidth=1)

ax.set_rmax(2.2)
ax.set_rticks([0.5, 1.0, 1.5, 2.0])
ax.set_rlabel_position(22.5)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0), frameon=True, fontsize=10)
ax.set_title('多模型评估指标泰勒图\n(角度=相关系数, 半径=标准差)', fontsize=14, pad=20)

plt.tight_layout()
plt.show()
