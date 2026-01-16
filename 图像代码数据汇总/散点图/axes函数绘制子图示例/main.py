# 胡涛 - axes()函数绘制子图示例结果
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
                if 'X' in df.columns and 'Y' in df.columns:
                    return df['X'].values, df['Y'].values
            except Exception:
                pass
    # 内置示例数据
    np.random.seed(42)
    x = np.linspace(0, 10, 100)
    y = np.sin(x)
    return x, y

x_data, y_data = load_data()

# 创建更多数据
x = np.linspace(0, 10, 100)
y1 = np.sin(x)
y2 = np.cos(x)
y3 = np.exp(-x/5) * np.sin(x)

# 创建主图形
fig = plt.figure(figsize=(12, 8))

# 主图
ax_main = fig.add_axes([0.1, 0.1, 0.65, 0.8])
ax_main.plot(x, y1, 'b-', linewidth=2, label='sin(x)')
ax_main.plot(x, y2, 'r-', linewidth=2, label='cos(x)')
ax_main.plot(x, y3, 'g-', linewidth=2, label='衰减正弦')
ax_main.set_xlabel('X', fontsize=12)
ax_main.set_ylabel('Y', fontsize=12)
ax_main.set_title('主图：axes()函数绘制子图示例', fontsize=14)
ax_main.legend(loc='upper right')
ax_main.grid(True, linestyle='--', alpha=0.3)

# 右上角小图1
ax_inset1 = fig.add_axes([0.78, 0.6, 0.2, 0.3])
ax_inset1.plot(x[:30], y1[:30], 'b-', linewidth=1.5)
ax_inset1.set_title('局部放大1', fontsize=10)
ax_inset1.set_xlim(0, 3)
ax_inset1.grid(True, linestyle='--', alpha=0.3)

# 右下角小图2
ax_inset2 = fig.add_axes([0.78, 0.15, 0.2, 0.3])
data = np.random.randn(100)
ax_inset2.hist(data, bins=15, color='#4DBBD5', edgecolor='white', alpha=0.7)
ax_inset2.set_title('数据分布', fontsize=10)

# 主图内嵌小图
ax_embedded = fig.add_axes([0.2, 0.55, 0.25, 0.25])
ax_embedded.scatter(x[::5], y3[::5], c='green', s=30, alpha=0.7)
ax_embedded.set_title('散点图', fontsize=9)
ax_embedded.set_facecolor('#f0f0f0')

plt.show()
