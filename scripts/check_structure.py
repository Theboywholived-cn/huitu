#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test without imports - directly verify the directory structure
"""
import os

templates_path = r"D:\文件夹\绘图\图像代码数据汇总"

print("🔍 Scanning new directory structure...")
print(f"Path: {templates_path}\n")

# First layer: chart types
chart_types = []
for item in os.listdir(templates_path):
    item_path = os.path.join(templates_path, item)
    if os.path.isdir(item_path) and not item.startswith('.'):
        chart_types.append(item)

print(f"✓ Found {len(chart_types)} chart types:")
for ct in sorted(chart_types):
    print(f"  • {ct}")

print("\n📊 Templates by chart type:\n")

total_templates = 0
for chart_type in sorted(chart_types):
    chart_type_path = os.path.join(templates_path, chart_type)
    
    templates_list = []
    for template_name in os.listdir(chart_type_path):
        template_dir = os.path.join(chart_type_path, template_name)
        
        if not os.path.isdir(template_dir):
            continue
        
        # Check for main.py
        main_py = os.path.join(template_dir, 'main.py')
        has_main = os.path.exists(main_py)
        
        # Check for data files
        data_files = [f for f in os.listdir(template_dir) 
                     if f.endswith(('.csv', '.xlsx', '.xls'))]
        has_data = len(data_files) > 0
        
        # Check for images
        has_image = False
        for f in os.listdir(template_dir):
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                has_image = True
                break
        
        templates_list.append({
            'name': template_name,
            'has_main': has_main,
            'has_data': has_data,
            'has_image': has_image,
            'data_files': data_files
        })
    
    if templates_list:
        print(f"📁 {chart_type} ({len(templates_list)} templates)")
        for t in templates_list:
            main_mark = "✓" if t['has_main'] else "✗"
            data_mark = "✓" if t['has_data'] else "✗"
            img_mark = "✓" if t['has_image'] else "✗"
            print(f"  {main_mark} {t['name']:35} [data:{data_mark}] [img:{img_mark}]", end='')
            if t['data_files']:
                print(f"  {t['data_files']}", end='')
            print()
        total_templates += len(templates_list)

print(f"\n✓ Total: {total_templates} templates")
