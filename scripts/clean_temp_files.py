#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 scripts/ 目录下由测试脚本生成的临时图片文件
匹配规则: test_*.png（不含原始示例图，不递归子目录）
"""
import os
import glob

SCRIPTS_DIR  = os.path.dirname(os.path.abspath(__file__))
PATTERN      = os.path.join(SCRIPTS_DIR, 'test_*.png')

targets = sorted(glob.glob(PATTERN))

if not targets:
    print('未找到需要清理的临时图片文件。')
else:
    print(f'找到 {len(targets)} 个临时图片文件:')
    for f in targets:
        print(f'  • {os.path.basename(f)}')

    confirm = input('\n确认删除以上文件？(y/N): ').strip().lower()
    if confirm == 'y':
        removed = 0
        for f in targets:
            try:
                os.remove(f)
                removed += 1
            except OSError as e:
                print(f'[错误] 无法删除 {f}: {e}')
        print(f'\n✓ 已删除 {removed} 个文件')
    else:
        print('已取消，未删除任何文件。')
