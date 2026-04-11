#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试热力图在不同配色方案下的渲染效果，输出对比图到当前目录"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

COLORMAPS  = ['viridis', 'plasma', 'coolwarm', 'RdYlGn', 'YlOrRd', 'Blues', 'hot']
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

np.random.seed(7)
rows_labels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
cols_labels = [f'{h:02d}:00' for h in range(0, 24, 3)]
data = np.random.randint(0, 100, size=(len(rows_labels), len(cols_labels)))

for cmap_name in COLORMAPS:
    fig, ax = plt.subplots(figsize=(10, 4), dpi=120)

    im = ax.imshow(data, cmap=cmap_name, aspect='auto')
    plt.colorbar(im, ax=ax, shrink=0.8)

    ax.set_xticks(range(len(cols_labels)))
    ax.set_xticklabels(cols_labels, fontsize=9)
    ax.set_yticks(range(len(rows_labels)))
    ax.set_yticklabels(rows_labels, fontsize=10)

    for i in range(len(rows_labels)):
        for j in range(len(cols_labels)):
            ax.text(j, i, str(data[i, j]),
                    ha='center', va='center', fontsize=7,
                    color='white' if data[i, j] < 50 else 'black')

    ax.set_title(f'热力图配色测试 — {cmap_name}', fontsize=13, fontweight='bold')
    fig.tight_layout()

    out_file = os.path.join(OUTPUT_DIR, f'test_heatmap_{cmap_name}.png')
    fig.savefig(out_file)
    plt.close(fig)
    print(f'已保存: {out_file}')

print(f'\n✓ 共生成 {len(COLORMAPS)} 张热力图配色对比图')
