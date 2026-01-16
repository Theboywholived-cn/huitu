# 多类别相关性（误差）散点图_a
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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
                if 'X' in df.columns and 'Y' in df.columns:
                    data = {}
                    cat_col = None
                    for col in ['类别', 'Category', 'Group', '组别']:
                        if col in df.columns:
                            cat_col = col
                            break
                    if cat_col:
                        for cat in df[cat_col].unique():
                            sub = df[df[cat_col] == cat]
                            x_err = sub['X_err'].values if 'X_err' in df.columns else np.random.uniform(0.1, 0.3, len(sub))
                            y_err = sub['Y_err'].values if 'Y_err' in df.columns else np.random.uniform(0.1, 0.4, len(sub))
                            data[cat] = (sub['X'].values, sub['Y'].values, x_err, y_err)
                    return data
            except Exception:
                pass
    # 内置示例数据
    np.random.seed(42)
    n = 30
    categories = ['类别A', '类别B', '类别C', '类别D']
    data = {}
    for i, cat in enumerate(categories):
        x = np.random.normal(i * 2, 0.8, n)
        y = x * (0.8 + i * 0.1) + np.random.normal(0, 0.5, n)
        x_err = np.random.uniform(0.1, 0.3, n)
        y_err = np.random.uniform(0.1, 0.4, n)
        data[cat] = (x, y, x_err, y_err)
    return data

# 加载数据
data = load_data()
colors = ['#E64B35', '#4DBBD5', '#00A087', '#F39B7F', '#3C5488', '#8491B4']

# 创建图形
fig, ax = plt.subplots(figsize=(10, 8))

for i, (cat, (x, y, x_err, y_err)) in enumerate(data.items()):
    color = colors[i % len(colors)]
    ax.errorbar(x, y, xerr=x_err, yerr=y_err, fmt='o', color=color,
               ecolor=color, elinewidth=1, capsize=3, capthick=1,
               markersize=8, alpha=0.7, label=cat)

ax.set_xlabel('X 变量', fontsize=12)
ax.set_ylabel('Y 变量', fontsize=12)
ax.set_title('多类别相关性散点图（带误差线）', fontsize=14)
ax.legend(loc='upper left', frameon=True, fancybox=True)
ax.grid(True, linestyle='--', alpha=0.3)

plt.tight_layout()
plt.show()
