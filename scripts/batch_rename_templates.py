#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量重命名模板子目录
将目录名中多余的空格、全角字符、括号等统一清理，
确保命名与后端扫描规则保持一致。
运行后会先预览变更列表，确认后再执行。
"""
import os
import re

TEMPLATES_ROOT = r'D:\文件夹\绘图\图像代码数据汇总'


def normalize_name(name: str) -> str:
    """标准化目录名：去首尾空格、合并连续空格、替换全角括号为半角"""
    name = name.strip()
    name = re.sub(r'\s+', ' ', name)          # 合并多余空格
    name = name.replace('（', '(').replace('）', ')')  # 全角→半角括号
    name = name.replace('【', '[').replace('】', ']')
    return name


if not os.path.exists(TEMPLATES_ROOT):
    print(f'[错误] 路径不存在: {TEMPLATES_ROOT}')
    exit(1)

renames = []

for chart_type in sorted(os.listdir(TEMPLATES_ROOT)):
    chart_dir = os.path.join(TEMPLATES_ROOT, chart_type)
    if not os.path.isdir(chart_dir):
        continue

    for tpl_name in sorted(os.listdir(chart_dir)):
        tpl_dir  = os.path.join(chart_dir, tpl_name)
        if not os.path.isdir(tpl_dir):
            continue

        new_name = normalize_name(tpl_name)
        if new_name != tpl_name:
            renames.append((tpl_dir, os.path.join(chart_dir, new_name)))

if not renames:
    print('✓ 所有模板目录命名规范，无需重命名。')
    exit(0)

print(f'发现 {len(renames)} 个需要重命名的目录:\n')
for old, new in renames:
    print(f'  旧: {os.path.basename(old)}')
    print(f'  新: {os.path.basename(new)}')
    print()

confirm = input('确认执行重命名？(y/N): ').strip().lower()
if confirm != 'y':
    print('已取消。')
    exit(0)

success = 0
for old, new in renames:
    try:
        os.rename(old, new)
        success += 1
        print(f'✓ {os.path.basename(old)} → {os.path.basename(new)}')
    except OSError as e:
        print(f'✗ 失败: {old} → {e}')

print(f'\n完成，共重命名 {success}/{len(renames)} 个目录。')
