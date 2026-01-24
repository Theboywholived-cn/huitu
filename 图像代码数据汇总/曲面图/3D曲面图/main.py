# 3D曲面图示例（Matplotlib版）
# 根据上传的数据生成3D曲面图
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata
import glob
import os
import sys

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# 读取配置
# ============================================================================
def get_config():
    default = {
        'x_column': None,
        'y_columns': None,
        'colormap': 'jet',
        'title': '3D曲面图',
        'x_label': 'X',
        'y_label': 'Y',
        'z_label': 'Z',
        'fig_width': 10,
        'fig_height': 8,
        'dpi': 150,
        'elev': 30,  # 仰角
        'azim': -60,  # 方位角
    }
    
    try:
        cfg = CHART_CONFIG
        for k in default:
            val = getattr(cfg, k, None)
            if val is not None:
                default[k] = val
    except NameError:
        pass
    
    if os.path.exists('_chart_config.json'):
        try:
            import json
            with open('_chart_config.json', 'r', encoding='utf-8') as f:
                cfg_json = json.load(f)
                for k in default:
                    if k in cfg_json and cfg_json[k] is not None:
                        default[k] = cfg_json[k]
        except Exception:
            pass
    
    return default

config = get_config()
print(f"配置: colormap={config['colormap']}")

# ============================================================================
# 加载数据
# ============================================================================
def load_data():
    """智能查找并加载数据文件"""
    files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    
    # 排除以下划线开头的文件
    files = [f for f in files if not f.startswith('_')]
    
    if not files:
        print(f"当前目录文件: {os.listdir('.')}")
        raise FileNotFoundError("未找到数据文件，请上传 .csv 或 .xlsx 文件")
    
    # 优先选择用户上传的文件（排除示范数据）
    target = files[0]
    for f in files:
        if "示范" not in f and "demo" not in f.lower():
            target = f
            break
    
    print(f"加载文件: {target}")
    
    if target.endswith('.csv'):
        for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
            try:
                return pd.read_csv(target, encoding=encoding)
            except:
                continue
        return pd.read_csv(target, encoding='utf-8', errors='replace')
    else:
        return pd.read_excel(target)

# 加载数据
df = load_data()
print(f"数据: {len(df)} 行, {len(df.columns)} 列")
print(f"列名: {list(df.columns)}")

# ============================================================================
# 提取数值列
# ============================================================================
df_numeric = df.select_dtypes(include=[np.number])
if df_numeric.shape[1] < 3:
    raise ValueError(f"数据需要至少3个数值列 (X, Y, Z)。当前只有: {df_numeric.columns.tolist()}")

# 获取 X, Y, Z 数据
x_col = df_numeric.columns[0]
y_col = df_numeric.columns[1]
z_col = df_numeric.columns[2]

x = df_numeric[x_col].values
y = df_numeric[y_col].values
z = df_numeric[z_col].values

print(f"使用列: X={x_col}, Y={y_col}, Z={z_col}")

# ============================================================================
# 创建网格并插值
# ============================================================================
# 创建规则网格
xi = np.linspace(x.min(), x.max(), 50)
yi = np.linspace(y.min(), y.max(), 50)
Xi, Yi = np.meshgrid(xi, yi)

# 使用三次插值生成平滑曲面
try:
    Zi = griddata((x, y), z, (Xi, Yi), method='cubic')
except:
    Zi = griddata((x, y), z, (Xi, Yi), method='linear')

# 填充 NaN 值（边缘区域）
Zi = np.nan_to_num(Zi, nan=np.nanmean(z))

# ============================================================================
# 绑制3D曲面图
# ============================================================================
fig = plt.figure(figsize=(config['fig_width'], config['fig_height']), dpi=config['dpi'])
ax = fig.add_subplot(111, projection='3d')

# 绑制曲面
surf = ax.plot_surface(Xi, Yi, Zi, 
                       cmap=config['colormap'],
                       edgecolor='none',
                       alpha=0.95,
                       antialiased=True,
                       rstride=1, cstride=1)

# 设置标签
ax.set_xlabel(config['x_label'] or x_col, fontsize=12, fontweight='bold')
ax.set_ylabel(config['y_label'] or y_col, fontsize=12, fontweight='bold')
ax.set_zlabel(config['z_label'] or z_col, fontsize=12, fontweight='bold')

# 设置标题
if config['title']:
    ax.set_title(config['title'], fontsize=14, fontweight='bold', pad=10)

# 设置视角
ax.view_init(elev=config['elev'], azim=config['azim'])

# 设置刻度标签大小
ax.tick_params(axis='both', which='major', labelsize=10)

# 调整布局
plt.tight_layout()

# 保存
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"\n图表已保存: output.png")
