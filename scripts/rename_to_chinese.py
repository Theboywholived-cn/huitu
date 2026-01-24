#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重命名图表类型目录为中文名称
"""
import os
import shutil

TEMPLATES_ROOT = r"D:\文件夹\绘图\图像代码数据汇总"

# 英文 → 中文映射
RENAME_MAP = {
    'taylor': '泰勒图',
    'scatter_cmap': '色标散点图',
    'scatter_multi': '散点对比图',
    'scatter': '散点图',
    'bar': '柱状图',
    'violin': '小提琴图',
    'boxplot': '箱线图',
    'heatmap': '热力图',
    'line_multi': '多曲线',
    'line': '折线图',
    'hist': '直方图',
    'other': '其他'
}

print("🔄 重命名图表类型目录为中文...")

for en_name, zh_name in RENAME_MAP.items():
    en_path = os.path.join(TEMPLATES_ROOT, en_name)
    zh_path = os.path.join(TEMPLATES_ROOT, zh_name)
    
    if os.path.exists(en_path) and not os.path.exists(zh_path):
        try:
            os.rename(en_path, zh_path)
            print(f"  ✓ {en_name:20} → {zh_name}")
        except Exception as e:
            print(f"  ✗ {en_name:20} → {zh_name}: {e}")
    elif os.path.exists(zh_path):
        print(f"  - {en_name:20} (已存在为 {zh_name})")

print("\n✓ 目录重命名完成")

# 验证
print("\n📁 新目录结构:")
dirs = [d for d in os.listdir(TEMPLATES_ROOT) if os.path.isdir(os.path.join(TEMPLATES_ROOT, d)) and not d.startswith('.')]
for d in sorted(dirs):
    count = len([x for x in os.listdir(os.path.join(TEMPLATES_ROOT, d)) if os.path.isdir(os.path.join(TEMPLATES_ROOT, d, x))])
    print(f"  • {d:20} ({count} 模板)")
