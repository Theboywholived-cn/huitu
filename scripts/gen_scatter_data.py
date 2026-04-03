#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成散点图/气泡图的示例数据"""
import pandas as pd
import random

random.seed(42)

n = 40
groups = ['组A', '组B', '组C', '组D']

rows = []
for i in range(n):
    group = groups[i % len(groups)]
    base  = (i % len(groups)) * 15
    rows.append({
        '分组':  group,
        'X轴数值': round(base + random.gauss(0, 5), 2),
        'Y轴数值': round(base + random.gauss(0, 8), 2),
        '气泡大小': random.randint(20, 200),
        '标签':  f'样本{i+1:02d}',
    })

df = pd.DataFrame(rows)

output_path = r'D:\文件夹\绘图\图像代码数据汇总\散点图\分组散点图\示范数据.xlsx'
df.to_excel(output_path, index=False)
print(f'已生成: {output_path}')
print(f'共 {len(df)} 条数据，分组: {groups}')
