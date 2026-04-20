#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出所有图表模板的清单到 Excel
输出字段: 图表类型、模板名称、是否有主程序、是否有数据、是否有预览图
"""
import os
import pandas as pd

TEMPLATES_ROOT = r'D:\文件夹\绘图\图像代码数据汇总'
OUTPUT_PATH    = r'D:\文件夹\绘图\chart_list.xlsx'

DATA_EXTS  = ('.xlsx', '.xls', '.csv')
IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.bmp')

rows = []

if not os.path.exists(TEMPLATES_ROOT):
    print(f'[错误] 路径不存在: {TEMPLATES_ROOT}')
    exit(1)

for chart_type in sorted(os.listdir(TEMPLATES_ROOT)):
    chart_dir = os.path.join(TEMPLATES_ROOT, chart_type)
    if not os.path.isdir(chart_dir):
        continue

    for tpl_name in sorted(os.listdir(chart_dir)):
        tpl_dir = os.path.join(chart_dir, tpl_name)
        if not os.path.isdir(tpl_dir):
            continue

        files = os.listdir(tpl_dir)
        has_main  = '是' if any(f == 'main.py'              for f in files) else '否'
        has_data  = '是' if any(f.lower().endswith(DATA_EXTS)  for f in files) else '否'
        has_image = '是' if any(f.lower().endswith(IMAGE_EXTS) for f in files) else '否'

        data_files = [f for f in files if f.lower().endswith(DATA_EXTS)]

        rows.append({
            '图表类型': chart_type,
            '模板名称': tpl_name,
            '有主程序': has_main,
            '有数据文件': has_data,
            '有预览图': has_image,
            '数据文件名': ', '.join(data_files) if data_files else '',
        })

df = pd.DataFrame(rows)
df.to_excel(OUTPUT_PATH, index=False)
print(f'已导出 {len(df)} 条模板记录 → {OUTPUT_PATH}')
