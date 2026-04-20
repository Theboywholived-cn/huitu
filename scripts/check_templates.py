#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查模板目录的完整性
- 验证每个模板是否包含 main.py、数据文件和预览图
- 统计缺失项并输出修复建议
"""
import os

TEMPLATES_ROOT = r'D:\文件夹\绘图\图像代码数据汇总'

REQUIRED_FILES = ['main.py']
DATA_EXTS = ('.xlsx', '.xls', '.csv')
IMAGE_EXTS = ('.png', '.jpg', '.jpeg')

missing_main = []
missing_data = []
missing_image = []
ok_count = 0

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
        has_main  = any(f == 'main.py' for f in files)
        has_data  = any(f.lower().endswith(DATA_EXTS) for f in files)
        has_image = any(f.lower().endswith(IMAGE_EXTS) for f in files)

        label = f'{chart_type}/{tpl_name}'
        if not has_main:
            missing_main.append(label)
        if not has_data:
            missing_data.append(label)
        if not has_image:
            missing_image.append(label)
        if has_main and has_data and has_image:
            ok_count += 1

print('=' * 50)
print(f'✓ 完整模板数量: {ok_count}')
print(f'✗ 缺少 main.py : {len(missing_main)}')
print(f'✗ 缺少数据文件 : {len(missing_data)}')
print(f'✗ 缺少预览图   : {len(missing_image)}')
print('=' * 50)

if missing_main:
    print('\n[缺少 main.py]')
    for m in missing_main:
        print(f'  • {m}')

if missing_data:
    print('\n[缺少数据文件]')
    for m in missing_data:
        print(f'  • {m}')

if missing_image:
    print('\n[缺少预览图]')
    for m in missing_image:
        print(f'  • {m}')
