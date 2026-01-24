# 泰勒图绘制示例
# 支持多种标记样式、颜色映射、标签显示
import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['font.family'] = 'sans-serif'

# ============================================================================
# 预设配色方案
# ============================================================================
COLOR_PALETTES = {
    'jet': ['#E64B35', '#4DBBD5', '#00A087', '#3C5488', '#F39B7F', '#8491B4'],
    'viridis': ['#440154', '#31688E', '#35B779', '#FDE725', '#26828E', '#1F9E89'],
    'plasma': ['#0D0887', '#7E03A8', '#CC4778', '#F89540', '#ED7953', '#FB9F3A'],
    'coolwarm': ['#3B4CC0', '#6788EE', '#9ABBFF', '#F7D4C9', '#F2A07B', '#B40426'],
    'RdYlBu': ['#D73027', '#F46D43', '#FDAE61', '#ABD9E9', '#74ADD1', '#4575B4'],
    'hot': ['#8B0000', '#FF0000', '#FF4500', '#FFA500', '#FFFF00', '#FFFFFF'],
}

# 标记样式映射
MARKER_MAP = {
    'circle': 'o',
    'square': 's',
    'diamond': 'D',
    'triangle': '^',
    'star': '*',
    'plus': '+',
    'x': 'x',
    'pentagon': 'p',
    'hexagon': 'h',
}

# ============================================================================
# 读取配置
# ============================================================================
def get_config():
    """获取图表配置"""
    default = {
        'colormap': 'jet',
        'colors': None,
        'title': '',
        'x_label': 'Observation',
        'y_label': 'Standard Deviation',
        'show_legend': True,
        'show_grid': True,
        'fig_width': 10,
        'fig_height': 10,
        'dpi': 150,
        'marker_size': 12,
        'marker_style': 'star',
        # 泰勒图专属配置
        'show_rmsd': True,          # 显示RMSD等值线
        'show_labels': True,        # 显示数据点标签
        'show_colorbar': False,     # 显示颜色条（用于第三变量映射）
        'use_different_markers': True,  # 使用不同标记区分模型
        'ref_std': 5.0,             # 参考观测值的标准差
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
print(f"配置: colormap={config['colormap']}, show_rmsd={config.get('show_rmsd', True)}")

# ============================================================================
# 加载数据
# ============================================================================
def load_data():
    """智能查找并加载数据文件"""
    files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    files = [f for f in files if not f.startswith('_')]
    
    if not files:
        # 内置示例数据 - 模拟图片中的数据结构
        return pd.DataFrame({
            'Model': ['PIR', 'NDIR', 'DIR', 'RIR', 'RIE', 'PIE', 'NDIE', 'DIE'],
            'Correlation': [0.95, 0.92, 0.90, 0.88, 0.94, 0.91, 0.89, 0.87],
            'StdDev': [2.2, 2.5, 2.8, 2.0, 2.1, 2.6, 3.0, 3.3],
            'RMSEP': [1.5, 1.8, 2.0, 1.6, 1.48, 1.9, 2.1, 2.28],
        })
    
    target = files[0]
    print(f"加载数据: {target}")
    
    if target.endswith('.csv'):
        for enc in ['utf-8', 'gbk', 'gb2312', 'latin1']:
            try:
                return pd.read_csv(target, encoding=enc)
            except:
                continue
        return pd.read_csv(target, encoding='utf-8', errors='replace')
    else:
        return pd.read_excel(target)

df = load_data()
print(f"数据: {len(df)} 行, {len(df.columns)} 列")
print(f"列名: {list(df.columns)}")

# ============================================================================
# 确定数据列
# ============================================================================
model_col = None
corr_col = None
std_col = None
color_col = None  # 用于颜色映射的第三个变量

for col in df.columns:
    col_lower = col.lower()
    if model_col is None and any(kw in col_lower for kw in ['model', 'name', '模型', '名称', 'label']):
        model_col = col
    elif corr_col is None and any(kw in col_lower for kw in ['corr', '相关', 'correlation']):
        corr_col = col
    elif std_col is None and any(kw in col_lower for kw in ['sd', 'std', 'dev', '标准差', 'sigma']):
        std_col = col
    elif color_col is None and any(kw in col_lower for kw in ['rmse', 'rmsep', 'error', '误差', 'value']):
        color_col = col

# 如果没找到，使用默认列
if model_col is None:
    non_numeric = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    model_col = non_numeric[0] if non_numeric else df.columns[0]

numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
if corr_col is None and len(numeric_cols) >= 1:
    corr_col = numeric_cols[0]
if std_col is None and len(numeric_cols) >= 2:
    std_col = numeric_cols[1]
if color_col is None and len(numeric_cols) >= 3:
    color_col = numeric_cols[2]

print(f"模型列: {model_col}, 相关系数列: {corr_col}, 标准差列: {std_col}, 颜色映射列: {color_col}")

# ============================================================================
# 获取配色
# ============================================================================
def get_colors(colormap_name, count):
    """根据配色方案获取颜色列表"""
    if colormap_name in COLOR_PALETTES:
        palette = COLOR_PALETTES[colormap_name]
        return [palette[i % len(palette)] for i in range(count)]
    else:
        try:
            cmap = plt.cm.get_cmap(colormap_name)
            return [cmap(i / max(count - 1, 1)) for i in range(count)]
        except:
            return COLOR_PALETTES['jet'][:count]

# ============================================================================
# 绑制泰勒图
# ============================================================================
fig = plt.figure(figsize=(config['fig_width'], config['fig_height']), dpi=config['dpi'])

# 使用极坐标
ax = fig.add_subplot(111, projection='polar')
ax.set_theta_zero_location('E')  # 0度在右边（东）
ax.set_theta_direction(1)        # 逆时针方向
ax.set_thetamin(0)
ax.set_thetamax(90)

# 参考标准差（观测值）
ref_std = config.get('ref_std', 5.0)
if ref_std <= 0:
    ref_std = df[std_col].max() * 1.2 if std_col else 5.0

# 计算合适的最大半径
max_std = df[std_col].max() if std_col else 5.0
r_max = max(ref_std, max_std) * 1.2

# ============================================================================
# 绘制相关系数径向线（黑色虚线）
# ============================================================================
corr_ticks = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]
for corr in corr_ticks:
    theta = np.arccos(corr)
    ax.plot([theta, theta], [0, r_max], 'k--', alpha=0.4, linewidth=0.8)

# 绘制相关系数标签（沿弧线）
for corr in corr_ticks[:-1]:  # 不标注1.0
    theta = np.arccos(corr)
    ax.text(theta, r_max * 1.05, f'{corr}', ha='center', va='bottom', 
           fontsize=10, fontstyle='italic')

# 相关系数标题
ax.text(np.pi/4, r_max * 1.25, 'Correlation Coefficient', ha='center', va='center',
       fontsize=12, fontstyle='italic', fontweight='bold', rotation=-45)

# ============================================================================
# 绘制标准差弧线（蓝色实线 - 以原点为圆心）
# ============================================================================
theta_range = np.linspace(0, np.pi/2, 100)
std_ticks = np.arange(0, r_max + 1, max(1, int(r_max / 5)))
for std_val in std_ticks:
    if std_val > 0:
        ax.plot(theta_range, np.full_like(theta_range, std_val), 'b-', 
               alpha=0.8, linewidth=1.5)

# 标准差标签（Y轴方向）
ax.set_ylabel(config['y_label'] or 'Standard Deviation', fontsize=14, 
             fontweight='bold', color='blue', labelpad=20)

# ============================================================================
# 绘制参考标准差弧线（红色实线）
# ============================================================================
ax.plot(theta_range, np.full_like(theta_range, ref_std), 'r-', 
       alpha=0.9, linewidth=2.5, label='Observation Std')

# ============================================================================
# 绘制RMSD等值线（绿色虚线 - 以参考点为圆心）
# ============================================================================
if config.get('show_rmsd', True):
    # RMSD等值线：以(theta=0, r=ref_std)为圆心的圆
    rmsd_ticks = [2.0, 4.0, 6.0]
    for rmsd in rmsd_ticks:
        if rmsd < r_max:
            theta_circle = np.linspace(0, np.pi/2, 200)
            r_circle = []
            valid_theta = []
            for t in theta_circle:
                # 使用余弦定理：c² = a² + b² - 2ab*cos(C)
                # 这里 a = ref_std, b = r, C = theta, c = rmsd
                # 所以 r² - 2*ref_std*cos(theta)*r + (ref_std² - rmsd²) = 0
                # 解二次方程
                a_coef = 1
                b_coef = -2 * ref_std * np.cos(t)
                c_coef = ref_std**2 - rmsd**2
                discriminant = b_coef**2 - 4 * a_coef * c_coef
                if discriminant >= 0:
                    r1 = (-b_coef + np.sqrt(discriminant)) / (2 * a_coef)
                    r2 = (-b_coef - np.sqrt(discriminant)) / (2 * a_coef)
                    for r in [r1, r2]:
                        if 0 < r <= r_max:
                            r_circle.append(r)
                            valid_theta.append(t)
                            break
            if len(r_circle) > 1:
                # 排序以确保连续
                sorted_pairs = sorted(zip(valid_theta, r_circle))
                valid_theta = [p[0] for p in sorted_pairs]
                r_circle = [p[1] for p in sorted_pairs]
                ax.plot(valid_theta, r_circle, 'g--', alpha=0.6, linewidth=1.5)
                # 标注RMSD值
                mid_idx = len(valid_theta) // 2
                ax.text(valid_theta[mid_idx], r_circle[mid_idx], f'{rmsd:.1f}', 
                       color='green', fontsize=10, fontstyle='italic')

    # RMSD标签
    ax.text(np.pi/6, r_max * 0.4, 'RMSD', color='green', fontsize=12, 
           fontstyle='italic', fontweight='bold', rotation=60)

# ============================================================================
# 绘制观测值参考点（红色圆点）
# ============================================================================
ax.plot(0, ref_std, 'ro', markersize=15, markeredgecolor='darkred', 
       markeredgewidth=2, zorder=10, label='Observation')

# ============================================================================
# 绘制模型数据点
# ============================================================================
models = df[model_col].values if model_col else [f'Model{i}' for i in range(len(df))]
correlations = df[corr_col].values if corr_col else np.random.uniform(0.8, 1.0, len(df))
std_devs = df[std_col].values if std_col else np.random.uniform(1, 5, len(df))
color_values = df[color_col].values if color_col and color_col in df.columns else None

# 可用的标记样式
available_markers = ['*', 'o', 'X', 's', 'D', '^', 'p', 'h', 'v', '<', '>']

# 是否使用颜色映射
use_colormap = config.get('show_colorbar', False) and color_values is not None

if use_colormap:
    # 使用颜色映射
    cmap = plt.cm.get_cmap(config['colormap'])
    norm = mcolors.Normalize(vmin=color_values.min(), vmax=color_values.max())
    
    for i, (model, corr, std, cval) in enumerate(zip(models, correlations, std_devs, color_values)):
        theta = np.arccos(np.clip(corr, -1, 1))
        marker = available_markers[i % len(available_markers)] if config.get('use_different_markers', True) else '*'
        color = cmap(norm(cval))
        
        ax.scatter(theta, std, s=config['marker_size']**2, c=[color], marker=marker,
                  edgecolors='black', linewidths=0.5, zorder=5)
        
        # 显示标签
        if config.get('show_labels', True):
            ax.text(theta, std + r_max * 0.03, model, ha='center', va='bottom',
                   fontsize=9, color=color, fontweight='bold')
    
    # 添加colorbar
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, pad=0.15, aspect=20)
    cbar.set_label(color_col or 'Value', fontsize=11)

else:
    # 使用离散颜色
    if config['colors'] and len(config['colors']) > 0:
        colors = config['colors']
    else:
        colors = get_colors(config['colormap'], len(models))
    
    for i, (model, corr, std) in enumerate(zip(models, correlations, std_devs)):
        theta = np.arccos(np.clip(corr, -1, 1))
        marker = available_markers[i % len(available_markers)] if config.get('use_different_markers', True) else '*'
        color = colors[i % len(colors)]
        
        ax.scatter(theta, std, s=config['marker_size']**2, c=[color], marker=marker,
                  edgecolors='black', linewidths=0.5, zorder=5, label=model)
        
        # 显示标签
        if config.get('show_labels', True):
            ax.text(theta, std + r_max * 0.03, model, ha='center', va='bottom',
                   fontsize=9, color=color, fontweight='bold')

# ============================================================================
# 设置坐标轴
# ============================================================================
ax.set_rmax(r_max)
ax.set_rticks(list(std_ticks))
ax.set_rlabel_position(0)  # 标签在0度位置

# X轴标签（Observation）
ax.set_xlabel(config['x_label'] or 'Observation', fontsize=14, fontweight='bold', 
             color='red', labelpad=10)

# 标题
if config['title']:
    ax.set_title(config['title'], fontsize=14, fontweight='bold', pad=20)

# 图例
if config['show_legend'] and not use_colormap:
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.0), frameon=True, 
             fontsize=9, ncol=1)

plt.tight_layout()
plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"图表已保存: output.png")
