#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试饼图/环形图在不同配色方案下的渲染效果，输出对比图到当前目录"""
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

COLORMAPS  = ['Set1', 'Set2', 'Set3', 'tab10', 'Paired', 'pastel1', 'Dark2']
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

labels = ['电子产品', '服装鞋帽', '食品饮料', '家居用品', '运动户外', '其他']
sizes  = [24.5, 16.4, 30.2, 12.1, 14.4, 6.3]

for cmap_name in COLORMAPS:
    try:
        cmap   = plt.get_cmap(cmap_name)
        colors = [cmap(i / len(labels)) for i in range(len(labels))]
    except ValueError:
        print(f'[跳过] 无效配色: {cmap_name}')
        continue

    fig, axes = plt.subplots(1, 2, figsize=(11, 5), dpi=120)

    # 左：普通饼图
    wedges, texts, autotexts = axes[0].pie(
        sizes, labels=labels, colors=colors,
        autopct='%1.1f%%', startangle=140,
        wedgeprops=dict(edgecolor='white', linewidth=1.2)
    )
    for at in autotexts:
        at.set_fontsize(9)
    axes[0].set_title(f'饼图 — {cmap_name}', fontsize=12, fontweight='bold')

    # 右：环形图
    axes[1].pie(
        sizes, labels=labels, colors=colors,
        autopct='%1.1f%%', startangle=140,
        wedgeprops=dict(width=0.55, edgecolor='white', linewidth=1.2)
    )
    axes[1].set_title(f'环形图 — {cmap_name}', fontsize=12, fontweight='bold')

    fig.tight_layout()
    out_file = os.path.join(OUTPUT_DIR, f'test_pie_{cmap_name}.png')
    fig.savefig(out_file)
    plt.close(fig)
    print(f'已保存: {out_file}')

print(f'\n✓ 共生成 {len(COLORMAPS)} 组配色对比图')
