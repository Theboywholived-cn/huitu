# 模型预测对比图绘制示例
# 多模型预测结果与真实值对比（横向子图布局）
import os
import json
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import r2_score, mean_absolute_error

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
        'colormap': 'jet',
        'colors': None,
        'title': '',
        'x_label': 'Clay Content (%)',
        'y_label': 'Depth (m)',
        'show_legend': True,
        'show_grid': True,
        'fig_width': 16,
        'fig_height': 6,
        'dpi': 150,
        # 模型对比图专属配置
        'true_color': '#0000FF',      # 真实值颜色 (蓝色)
        'pred_color': '#FF0000',      # 预测值颜色 (红色)
        'line_width': 1.0,            # 线宽
        'show_metrics': True,         # 显示R²和MAE指标
        'invert_y': True,             # Y轴反向（深度向下递增）
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
print(f"配置: show_metrics={config.get('show_metrics', True)}, invert_y={config.get('invert_y', True)}")

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
        n = 400
        depth = np.linspace(1600, 2000, n)
        base = 35 + 5 * np.sin(depth * 0.02)
        true_values = base + np.random.normal(0, 2, n)
        
        data = {'Depth': depth, 'True': true_values}
        for name in ['XGBoost', 'FCN', 'LSTM', 'CNN-LSTM', 'MLR']:
            data[name] = true_values + np.random.normal(0, 2, n)
        return pd.DataFrame(data)
    
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

df = load_data()
print(f"数据: {len(df)} 行, {len(df.columns)} 列")
print(f"列名: {list(df.columns)}")

# ============================================================================
# 识别数据列
# ============================================================================
# 识别深度/索引列（Y轴）
depth_col = None
for col in df.columns:
    if any(k in col.lower() for k in ['depth', '深度', 'index', '序号']):
        depth_col = col
        break

# 如果没找到深度列，使用索引
if not depth_col:
    df['_index'] = np.arange(len(df))
    depth_col = '_index'

# 识别真实值列
true_col = None
for col in df.columns:
    if col == depth_col or col == '_index':
        continue
    if any(k in col.lower() for k in ['true', '真实', 'actual', '实测', 'observed']):
        true_col = col
        break

# 识别模型预测列（排除深度列和真实值列和内部索引列）
model_cols = []
for col in df.columns:
    if col == depth_col or col == true_col or col == '_index':
        continue
    if pd.api.types.is_numeric_dtype(df[col]):
        model_cols.append(col)

# 如果没有识别到真实值列，使用第一个数值列
if not true_col:
    numeric_cols = [c for c in df.columns if c != depth_col and c != '_index' and pd.api.types.is_numeric_dtype(df[c])]
    if numeric_cols:
        true_col = numeric_cols[0]
        model_cols = numeric_cols[1:]

# 如果仍然没有模型列，但有预测值列，使用它
if not model_cols:
    for col in df.columns:
        if col == depth_col or col == true_col or col == '_index':
            continue
        if any(k in col.lower() for k in ['pred', '预测', 'forecast', 'estimate']):
            model_cols.append(col)
            break

# 如果只有2列数据（真实值和预测值），特殊处理
if not model_cols and len(df.columns) == 2:
    cols = df.columns.tolist()
    true_col = cols[0]
    model_cols = [cols[1]]
    df['_index'] = np.arange(len(df))
    depth_col = '_index'

print(f"深度列: {depth_col}, 真实值列: {true_col}")
print(f"模型列: {model_cols}")

if not true_col or not model_cols:
    raise ValueError("需要至少一个真实值列和一个模型预测列")

# ============================================================================
# 绑制多模型对比图
# ============================================================================
n_models = len(model_cols)
fig, axes = plt.subplots(1, n_models, figsize=(config['fig_width'], config['fig_height']), 
                          sharey=True)

# 如果只有一个模型，确保axes是列表
if n_models == 1:
    axes = [axes]

depth = df[depth_col].values
true_values = df[true_col].values

true_color = config.get('true_color', '#0000FF')
pred_color = config.get('pred_color', '#FF0000')
line_width = config.get('line_width', 1.0)
show_metrics = config.get('show_metrics', True)
invert_y = config.get('invert_y', True)

for i, (ax, model_name) in enumerate(zip(axes, model_cols)):
    pred_values = df[model_name].values
    
    # 绑制真实值和预测值曲线
    ax.plot(true_values, depth, color=true_color, linewidth=line_width, label='True')
    ax.plot(pred_values, depth, color=pred_color, linewidth=line_width, label=f'{model_name} Pred')
    
    # 计算指标
    if show_metrics:
        try:
            r2 = r2_score(true_values, pred_values)
            mae = mean_absolute_error(true_values, pred_values)
            # 在右上角显示指标
            ax.text(0.95, 0.95, f'R² = {r2:.3f}\nMAE = {mae:.2f}',
                   transform=ax.transAxes, fontsize=9,
                   verticalalignment='top', horizontalalignment='right',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        except Exception:
            pass
    
    # 设置标题
    ax.set_title(f'{model_name} Model', fontsize=11, fontweight='bold')
    
    # 设置X轴标签
    ax.set_xlabel(config['x_label'], fontsize=10)
    
    # 只在第一个子图显示Y轴标签和图例
    if i == 0:
        ax.set_ylabel(config['y_label'], fontsize=10)
        if config['show_legend']:
            ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
    
    # Y轴反向（深度向下递增）
    if invert_y:
        ax.invert_yaxis()
    
    # 网格
    if config['show_grid']:
        ax.grid(True, linestyle='-', alpha=0.3)
    
    # 设置边框
    for spine in ax.spines.values():
        spine.set_linewidth(0.5)

# 调整布局
plt.tight_layout()

# 总标题
if config['title']:
    fig.suptitle(config['title'], fontsize=14, fontweight='bold', y=1.02)

plt.savefig('output.png', dpi=config['dpi'], bbox_inches='tight', facecolor='white')
plt.close()

print(f"\n图表已保存: output.png")
