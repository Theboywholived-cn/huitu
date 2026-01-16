#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix the generateCode function in ChartConfigurator.vue"""
import re

VUE_FILE = r'D:\文件夹\绘图\frontend\src\components\ChartConfigurator.vue'

NEW_FUNC = r'''// 生成 Python 代码
function generateCode(): string {
  const markerMap: Record<string, string> = {
    'circle': 'o', 'square': 's', 'triangle': '^',
    'diamond': 'D', 'star': '*', 'plus': '+', 'cross': 'x'
  }
  const marker = markerMap[config.value.markerShape] || 'o'
  const rows = config.value.gridRows
  const cols = config.value.gridCols
  const pairs = detectedPairs.value.slice(0, Math.max(0, config.value.chartCount))
  const pairsJson = JSON.stringify(pairs)
  const dataFileName = uploadedFileContent.value
    ? ((uploadedFile.value?.name || 'uploaded.csv').toLowerCase().endsWith('.csv')
        ? (uploadedFile.value?.name || 'uploaded.csv')
        : 'uploaded.csv')
    : (config.value.dataFile || 'data.csv')
  const showFormulas = config.value.showFormulas ? 'True' : 'False'
  const code = `# 自动生成的绘图代码
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

try:
    from scipy.stats import gaussian_kde
except:
    gaussian_kde = None

def _r2_score(y_true, y_pred):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - ss_res / ss_tot if ss_tot != 0 else float('nan')

def _rmse(y_true, y_pred):
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))

PAIRS = ${pairsJson}
DATA_FILE = r"${dataFileName}"
MARKER = '${marker}'
MARKER_SIZE = ${config.value.markerSize}
SHOW_LABELS = ${config.value.showLabels ? 'True' : 'False'}
SHOW_TITLE = ${config.value.showTitle ? 'True' : 'False'}
TITLE_TEXT = '${config.value.titleText}'
USE_COLORBAR = ${config.value.useColorbar ? 'True' : 'False'}
COLORBAR_MIN = ${config.value.colorbarMin ?? 'None'}
COLORBAR_MAX = ${config.value.colorbarMax ?? 'None'}
COLORMAP = '${config.value.colormap}'
SHOW_FORMULAS = ${showFormulas}

fig, axes = plt.subplots(${rows}, ${cols}, figsize=(${cols * 4.5}, ${rows * 4}))
if ${rows * cols} == 1:
    axes = np.array([axes])
axes = axes.flatten()

df = pd.read_csv(DATA_FILE)
if not PAIRS:
    raise RuntimeError('未检测到配对列')

n_charts = len(PAIRS)
sc_for_cbar = None

for i, p in enumerate(PAIRS):
    ax = axes[i]
    col_pred, col_true = p['col0'], p['col1']
    name = p.get('name', f'图{i+1}')
    x = pd.to_numeric(df[col_true], errors='coerce').to_numpy()
    y = pd.to_numeric(df[col_pred], errors='coerce').to_numpy()
    mask = np.isfinite(x) & np.isfinite(y)
    x, y = x[mask], y[mask]
    z = None
    if gaussian_kde and len(x) >= 5:
        try:
            xy = np.vstack([x, y])
            z = gaussian_kde(xy)(xy)
            idx = np.argsort(z)
            x, y, z = x[idx], y[idx], z[idx]
        except:
            pass
    if z is not None:
        sc = ax.scatter(x, y, c=z, cmap=COLORMAP, marker=MARKER, s=MARKER_SIZE**2, vmin=COLORBAR_MIN, vmax=COLORBAR_MAX)
        sc_for_cbar = sc
    else:
        ax.scatter(x, y, color='#1f77b4', marker=MARKER, s=MARKER_SIZE**2)
    if len(x) > 0:
        vmin, vmax = float(min(x.min(), y.min())), float(max(x.max(), y.max()))
        pad = (vmax - vmin) * 0.05 or 1.0
        ax.plot([vmin-pad, vmax+pad], [vmin-pad, vmax+pad], 'k-', lw=1)
        ax.set_xlim(vmin-pad, vmax+pad)
        ax.set_ylim(vmin-pad, vmax+pad)
    if len(x) >= 2:
        k, b = np.polyfit(x, y, 1)
        xs = np.array([x.min(), x.max()])
        ax.plot(xs, k*xs+b, 'r-', lw=1)
        r2, rmse = _r2_score(x, y), _rmse(x, y)
        if SHOW_FORMULAS:
            ax.text(0.05, 0.88, f'y = {k:.3f}x + {b:.3f}', transform=ax.transAxes, fontsize=9)
            ax.text(0.05, 0.78, f'R² = {r2:.2f}', transform=ax.transAxes, fontsize=9)
            ax.text(0.05, 0.68, f'RMSE = {rmse:.2f}', transform=ax.transAxes, fontsize=9)
    if SHOW_TITLE:
        t = str(name)
        for pf in ['PHIT', 'PHI', 'phi']:
            if t.startswith(pf): t = t[len(pf):]
        ax.set_title(t.lstrip('_') or name, fontweight='bold')
    if SHOW_LABELS:
        ax.set_xlabel('实测值')
        ax.set_ylabel('预测值')

for i in range(n_charts, len(axes)):
    axes[i].set_visible(False)

if SHOW_TITLE and TITLE_TEXT:
    fig.suptitle(TITLE_TEXT, fontsize=14, fontweight='bold')

if USE_COLORBAR and sc_for_cbar is not None:
    fig.colorbar(sc_for_cbar, ax=axes[:n_charts], fraction=0.03, pad=0.02, label='Density')

plt.tight_layout()
plt.savefig('output.png', dpi=150, bbox_inches='tight', facecolor='white')
plt.close()
`
  return code
}'''

with open(VUE_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the generateCode function - more flexible pattern
start_marker = '// 生成 Python 代码\nfunction generateCode(): string {'
end_marker = '\n  return code\n}'

start_idx = content.find(start_marker)
if start_idx == -1:
    print("Cannot find start marker")
    exit(1)

# Find the end by searching for return code after the start
search_from = start_idx + len(start_marker)
end_idx = content.find(end_marker, search_from)
if end_idx == -1:
    print("Cannot find end marker")
    exit(1)

end_idx += len(end_marker)

# Replace
new_content = content[:start_idx] + NEW_FUNC + content[end_idx:]

with open(VUE_FILE, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("SUCCESS: generateCode function replaced!")
print(f"Replaced {end_idx - start_idx} chars with {len(NEW_FUNC)} chars")
