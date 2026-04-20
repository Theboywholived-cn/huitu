#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试柱状图在不同配色方案下的渲染效果，输出对比图到当前目录"""
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

COLORMAPS = ['Set1', 'Set2', 'Set3', 'tab10', 'Paired', 'viridis', 'plasma']
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

categories = ['类别A', '类别B', '类别C', '类别D', '类别E']
values     = [42, 67, 35, 58, 50]
x = np.arange(len(categories))

for cmap_name in COLORMAPS:
    cmap   = plt.get_cmap(cmap_name)
    colors = [cmap(i / len(categories)) for i in range(len(categories))]

    fig, ax = plt.subplots(figsize=(7, 4), dpi=120)
    bars = ax.bar(x, values, color=colors, width=0.6, edgecolor='white', linewidth=0.8)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.8,
                str(val),
                ha='center', va='bottom', fontsize=10)

    ax.set_xticks(x)
    ax.set_xticklabels(categories, fontsize=11)
    ax.set_ylabel('数值', fontsize=11)
    ax.set_title(f'柱状图配色测试 — {cmap_name}', fontsize=13, fontweight='bold')
    ax.set_ylim(0, max(values) * 1.2)
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    out_file = os.path.join(OUTPUT_DIR, f'test_bar_{cmap_name}.png')
    fig.tight_layout()
    fig.savefig(out_file)
    plt.close(fig)
    print(f'已保存: {out_file}')

print(f'\n✓ 共生成 {len(COLORMAPS)} 张配色对比图')
