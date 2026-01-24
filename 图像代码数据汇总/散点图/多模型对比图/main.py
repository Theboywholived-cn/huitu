# 多模型预测效果对比图 - 支持配置
# 自动识别配对列（如 XXX_0/XXX_1 或 实测值/预测值）生成密度散点对比图
import os
import json
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from scipy.stats import gaussian_kde
from scipy import stats

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# 读取配置
# ============================================================================

# Marker 转换映射（支持前端传入的名称和matplotlib符号）
MARKER_MAP = {
    'circle': 'o', 'o': 'o',
    'square': 's', 's': 's',
    'diamond': 'D', 'D': 'D',
    'triangle': '^', '^': '^',
    'star': '*', '*': '*',
    'plus': '+', '+': '+',
    'x': 'x',
}

def get_config():
    default = {
        'x_column': None,
        'y_columns': None,
        'group_column': None,
        'selected_pairs': None,  # 用户选择的配对名称列表
        'marker_style': 'o',
        'marker_size': 6,
        'line_style': '-',
        'line_width': 1.5,
        'colors': None,
        'colormap': 'jet',
        'title': '多模型预测效果对比',
        'x_label': '',
        'y_label': '',
        'show_legend': True,
        'show_grid': True,
        'fig_width': 12,
        'fig_height': 10,
        'dpi': 150
    }
    
    try:
        cfg = CHART_CONFIG
        result = {}
        for k in default:
            val = getattr(cfg, k, default[k])
            result[k] = val if val is not None else default[k]
        return result
    except NameError:
        pass
    
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

# 转换 marker_style 为 matplotlib 符号
config['marker_style'] = MARKER_MAP.get(config['marker_style'], config['marker_style'])

# 打印配置信息
print(f"配置: marker={config['marker_style']}, size={config['marker_size']}, colormap={config['colormap']}, line={config['line_style']}")

# ============================================================================
# 数据加载
# ============================================================================
def load_data():
    """加载数据文件"""
    for fname in os.listdir('.'):
        if fname.startswith('_'):
            continue
        ext = fname.split('.')[-1].lower()
        if ext == 'csv':
            for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
                try:
                    return pd.read_csv(fname, encoding=encoding)
                except:
                    continue
        elif ext in ['xlsx', 'xls']:
            try:
                return pd.read_excel(fname)
            except:
                continue
    
    # 示例数据
    np.random.seed(42)
    n = 100
    true_vals = np.linspace(0, 100, n)
    return pd.DataFrame({
        'PHIT_实测': true_vals,
        'XGBoost_预测': true_vals + np.random.normal(0, 5, n),
        'FCN_预测': true_vals + np.random.normal(2, 10, n),
        'LSTM_预测': true_vals + np.random.normal(-1, 7, n),
        'CNN_LSTM_预测': true_vals + np.random.normal(0.5, 4, n)
    })

df = load_data()
print(f"加载数据: {len(df)} 行, {len(df.columns)} 列")
print(f"列名: {list(df.columns)}")

# ============================================================================
# 自动识别配对列
# ============================================================================
def find_model_pairs(columns):
    """
    自动识别配对的列，支持多种命名规则：
    1. XXX_0 / XXX_1 模式（0是实测，1是预测）
    2. 实测值 / XXX预测 模式
    3. XXX_实测 / XXX_预测 模式
    """
    pairs = []
    col_list = list(columns)
    
    # 模式1: XXX_0 / XXX_1 (提取模型名)
    pattern_01 = {}
    for col in col_list:
        # 匹配如 PHITXGBoost_0, PHITCNN_LSTM_0 等
        match = re.match(r'^(.+?)_([01])$', col)
        if match:
            base, suffix = match.groups()
            if base not in pattern_01:
                pattern_01[base] = {}
            pattern_01[base][suffix] = col
    
    for base, suffixes in pattern_01.items():
        if '0' in suffixes and '1' in suffixes:
            # 提取模型名（去掉PHIT等前缀）
            model_name = base
            for prefix in ['PHIT', 'PHI', 'PH']:
                if model_name.startswith(prefix):
                    model_name = model_name[len(prefix):]
                    break
            # 处理下划线
            model_name = model_name.replace('_', '-')
            if not model_name:
                model_name = base
            
            pairs.append({
                'name': model_name,
                'x_col': suffixes['0'],  # 实测值
                'y_col': suffixes['1'],  # 预测值
            })
    
    # 模式2: 实测值列 + 多个预测列
    if not pairs:
        actual_col = None
        for col in col_list:
            if '实测' in col or 'actual' in col.lower() or 'true' in col.lower():
                actual_col = col
                break
        
        if actual_col:
            for col in col_list:
                if col == actual_col:
                    continue
                if '预测' in col or 'pred' in col.lower():
                    model_name = col.replace('预测值', '').replace('预测', '').replace('_', '').strip()
                    if not model_name:
                        model_name = col
                    pairs.append({
                        'name': model_name,
                        'x_col': actual_col,
                        'y_col': col,
                    })
    
    return pairs

pairs = find_model_pairs(df.columns)
print(f"识别到 {len(pairs)} 个模型配对:")
for p in pairs:
    print(f"  - {p['name']}: {p['x_col']} vs {p['y_col']}")

if not pairs:
    print("警告: 未能识别数据配对")
    raise ValueError("无法识别数据列配对，请确保列名包含 _0/_1 后缀或 实测/预测 关键字")

# 根据用户选择过滤配对
selected_pairs = config.get('selected_pairs')
if selected_pairs and len(selected_pairs) > 0:
    pairs = [p for p in pairs if p['name'] in selected_pairs]
    print(f"用户选择了 {len(pairs)} 个模型: {selected_pairs}")

# 限制最多4个子图
pairs = pairs[:4]

# ============================================================================
# 绑定图表
# ============================================================================
n_pairs = len(pairs)

# 计算子图布局
if n_pairs == 1:
    nrows, ncols = 1, 1
elif n_pairs == 2:
    nrows, ncols = 1, 2
elif n_pairs <= 4:
    nrows, ncols = 2, 2
else:
    nrows, ncols = 2, 3

fig, axes = plt.subplots(nrows, ncols, figsize=(config['fig_width'], config['fig_height']), dpi=config['dpi'])
if n_pairs == 1:
    axes = np.array([axes])
axes = axes.flatten()

# 隐藏多余的子图
for i in range(n_pairs, len(axes)):
    axes[i].set_visible(False)

# 绘制每个模型的对比图
for idx, pair in enumerate(pairs):
    ax = axes[idx]
    
    x_data = df[pair['x_col']].dropna().values.astype(float)
    y_data = df[pair['y_col']].dropna().values.astype(float)
    
    # 确保数据长度一致
    min_len = min(len(x_data), len(y_data))
    x_data = x_data[:min_len]
    y_data = y_data[:min_len]
    
    # 计算密度
    try:
        xy = np.vstack([x_data, y_data])
        density = gaussian_kde(xy)(xy)
        # 归一化密度
        density = (density - density.min()) / (density.max() - density.min() + 1e-10)
    except:
        density = np.ones(len(x_data))
    
    # 按密度排序（低密度先画，高密度后画）
    idx_sort = np.argsort(density)
    x_sorted = x_data[idx_sort]
    y_sorted = y_data[idx_sort]
    density_sorted = density[idx_sort]
    
    # 绘制散点（带密度颜色）
    scatter = ax.scatter(x_sorted, y_sorted, 
                        c=density_sorted, 
                        cmap=config['colormap'],
                        s=config['marker_size'] ** 2,
                        marker=config['marker_style'],
                        alpha=0.8,
                        edgecolors='none')
    
    # 计算数据范围
    all_data = np.concatenate([x_data, y_data])
    data_min = np.floor(all_data.min())
    data_max = np.ceil(all_data.max())
    margin = (data_max - data_min) * 0.05
    plot_min = data_min - margin
    plot_max = data_max + margin
    
    # 绘制1:1对角线（黑色，使用配置的线条样式）
    ax.plot([plot_min, plot_max], [plot_min, plot_max], 
            color='black', linestyle=config['line_style'], linewidth=config['line_width'])
    
    # 线性回归
    slope, intercept, r_value, p_value, std_err = stats.linregress(x_data, y_data)
    r_squared = r_value ** 2
    
    # 绘制回归线（红色，使用配置的线条样式）
    x_fit = np.array([plot_min, plot_max])
    y_fit = slope * x_fit + intercept
    ax.plot(x_fit, y_fit, color='red', linestyle=config['line_style'], linewidth=config['line_width'])
    
    # 计算RMSE
    rmse = np.sqrt(np.mean((y_data - x_data) ** 2))
    
    # 添加统计信息文本
    text_x = plot_min + (plot_max - plot_min) * 0.05
    text_y = plot_max - (plot_max - plot_min) * 0.05
    
    stats_text = f'y = {slope:.3f}x + {intercept:.3f}\n$R^2$ = {r_squared:.2f}\nRMSE = {rmse:.2f}'
    ax.text(text_x, text_y, stats_text, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    # 设置标题
    ax.set_title(pair['name'], fontsize=14, fontweight='bold')
    
    # 设置坐标轴
    ax.set_xlim(plot_min, plot_max)
    ax.set_ylim(plot_min, plot_max)
    ax.set_aspect('equal')
    
    # 设置标签
    ax.set_xlabel('实测值', fontsize=11)
    ax.set_ylabel('预测值', fontsize=11)
    
    # 添加子图标签
    ax.text(0.95, 0.05, f'({chr(97+idx)})', transform=ax.transAxes, 
            fontsize=12, fontweight='bold', ha='right', va='bottom')

# 添加colorbar
if n_pairs > 0:
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    sm = plt.cm.ScalarMappable(cmap=config['colormap'], norm=Normalize(vmin=0, vmax=1))
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax)
    cbar.set_label('Density', fontsize=11)

# 设置总标题
title = config['title'] or '多模型预测效果对比'
fig.suptitle(title, fontsize=16, fontweight='bold', y=0.98)

plt.subplots_adjust(left=0.08, right=0.88, top=0.92, bottom=0.08, wspace=0.25, hspace=0.25)
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"\n图表已保存: output.png")
