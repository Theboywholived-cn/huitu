# axes()函数绘制子图示例
# 多子图热力图 + 共享Colorbar
import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# 读取配置
# ============================================================================
def get_config():
    """获取图表配置"""
    default = {
        'colormap': 'viridis',
        'colors': None,
        'title': '',
        'x_label': '',
        'y_label': '',
        'show_legend': False,
        'show_grid': False,
        'fig_width': 10,
        'fig_height': 6,
        'dpi': 150,
        # 子图专属配置
        'n_subplots': 2,          # 子图数量
        'subplot_layout': 'vertical',  # 布局: vertical, horizontal
        'show_colorbar': True,    # 显示colorbar
        'share_colorbar': True,   # 共享colorbar
    }
    
    # 从 CHART_CONFIG 读取
    try:
        cfg = CHART_CONFIG
        for k in default:
            val = getattr(cfg, k, None)
            if val is not None:
                default[k] = val
    except NameError:
        # 从 JSON 文件读取
        if os.path.exists('_chart_config.json'):
            try:
                with open('_chart_config.json', 'r', encoding='utf-8') as f:
                    cfg_json = json.load(f)
                    for k in default:
                        if k in cfg_json and cfg_json[k] is not None:
                            default[k] = cfg_json[k]
            except Exception:
                pass
    
    return default

config = get_config()
print(f"配置: colormap={config['colormap']}, n_subplots={config.get('n_subplots', 2)}")

# ============================================================================
# 加载数据
# ============================================================================
def load_data():
    """智能查找并加载数据文件"""
    files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    files = [f for f in files if not f.startswith('_')]
    
    if not files:
        print("未找到数据文件，使用示例数据")
        np.random.seed(42)
        # 生成两个随机矩阵
        data1 = np.random.rand(100, 100)
        data2 = np.random.rand(100, 100)
        return [data1, data2], ['子图 1', '子图 2']
    
    target = files[0]
    for f in files:
        if "示范" not in f and "demo" not in f.lower():
            target = f
            break
    
    print(f"加载文件: {target}")
    
    try:
        if target.endswith('.csv'):
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                try:
                    df = pd.read_csv(target, encoding=encoding)
                    break
                except:
                    continue
            else:
                df = pd.read_csv(target, encoding='utf-8', errors='replace')
        else:
            # 尝试读取多个sheet
            xls = pd.ExcelFile(target)
            if len(xls.sheet_names) >= 2:
                # 多个sheet作为多个子图数据
                matrices = []
                titles = []
                for sheet in xls.sheet_names[:4]:  # 最多4个子图
                    df_sheet = pd.read_excel(target, sheet_name=sheet)
                    matrices.append(df_sheet.values)
                    titles.append(sheet)
                return matrices, titles
            else:
                df = pd.read_excel(target)
        
        # 单个sheet的数据处理
        # 如果是矩阵数据，直接使用
        if df.shape[0] > 10 and df.shape[1] > 10:
            # 看起来像矩阵数据
            half = len(df) // 2
            data1 = df.iloc[:half, :].values.astype(float)
            data2 = df.iloc[half:, :].values.astype(float)
            return [data1, data2], ['子图 1', '子图 2']
        else:
            # 生成示例数据
            np.random.seed(42)
            data1 = np.random.rand(100, 100)
            data2 = np.random.rand(100, 100)
            return [data1, data2], ['子图 1', '子图 2']
            
    except Exception as e:
        print(f"加载数据失败: {e}")
        np.random.seed(42)
        data1 = np.random.rand(100, 100)
        data2 = np.random.rand(100, 100)
        return [data1, data2], ['子图 1', '子图 2']

matrices, titles = load_data()
n_plots = len(matrices)
print(f"数据: {n_plots} 个子图矩阵")

# ============================================================================
# 绑制多子图热力图
# ============================================================================
n_subplots = min(config.get('n_subplots', 2), n_plots)
layout = config.get('subplot_layout', 'vertical')
show_colorbar = config.get('show_colorbar', True)
share_colorbar = config.get('share_colorbar', True)

# 设置图形尺寸
fig_width = config['fig_width']
fig_height = config['fig_height']

# 创建图形
fig = plt.figure(figsize=(fig_width, fig_height))

# 根据布局确定子图位置
if layout == 'vertical':
    # 垂直排列
    plot_height = 0.85 / n_subplots
    gap = 0.05
    axes_list = []
    for i in range(n_subplots):
        top = 0.9 - i * (plot_height + gap)
        ax = fig.add_axes([0.08, top - plot_height, 0.7, plot_height])
        axes_list.append(ax)
else:
    # 水平排列
    plot_width = 0.7 / n_subplots
    gap = 0.03
    axes_list = []
    for i in range(n_subplots):
        left = 0.08 + i * (plot_width + gap)
        ax = fig.add_axes([left, 0.1, plot_width, 0.8])
        axes_list.append(ax)

# 获取colormap
cmap = config['colormap']
if config['colors'] and len(config['colors']) > 0:
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list('custom', config['colors'])

# 计算全局vmin/vmax用于共享colorbar
if share_colorbar:
    all_data = np.concatenate([m.flatten() for m in matrices[:n_subplots]])
    vmin, vmax = np.nanmin(all_data), np.nanmax(all_data)
else:
    vmin, vmax = None, None

# 绑制每个子图
im = None
for i, ax in enumerate(axes_list):
    if i < len(matrices):
        data = matrices[i]
        # 确保数据是数值类型
        try:
            data = np.array(data, dtype=float)
        except:
            data = np.random.rand(100, 100)
        
        if share_colorbar:
            im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=vmin, vmax=vmax)
        else:
            im = ax.imshow(data, cmap=cmap, aspect='auto')
        
        # 标题
        if i < len(titles):
            ax.set_title(titles[i], fontsize=11)
        
        # 设置刻度
        ax.tick_params(labelsize=9)

# 添加colorbar
if show_colorbar and im is not None:
    if layout == 'vertical':
        cbar_ax = fig.add_axes([0.82, 0.1, 0.03, 0.8])
    else:
        cbar_ax = fig.add_axes([0.82, 0.1, 0.03, 0.8])
    
    cbar = fig.colorbar(im, cax=cbar_ax)
    cbar.ax.tick_params(labelsize=10)

# 设置总标题
if config['title']:
    fig.suptitle(config['title'], fontsize=14, fontweight='bold', y=0.98)

plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"\n图表已保存: output.png")
