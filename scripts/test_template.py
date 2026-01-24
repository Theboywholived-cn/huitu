#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试模板执行"""
import requests
import json
import os

url = 'http://127.0.0.1:8000/api/templates/run-configured'

# 测试1: 显示误差线
config1 = {
    'colormap': 'Set1',
    'show_points': True,
    'show_error': True,
    'error_type': 'sd',
    'bar_width': 0.8,
    'point_size': 5,
    'fig_width': 10,
    'fig_height': 8,
    'dpi': 150
}

# 测试2: 不显示误差线
config2 = {
    'colormap': 'Set1',
    'show_points': True,
    'show_error': False,
    'error_type': 'sd',
    'bar_width': 0.8,
    'point_size': 5,
    'fig_width': 10,
    'fig_height': 8,
    'dpi': 150
}

data_file = r'D:\文件夹\绘图\图像代码数据汇总\多曲线\分组误差柱形图\分组误差柱形图数据.xlsx'

for i, config in enumerate([config1, config2], 1):
    print(f"\n测试{i}: show_error={config['show_error']}")
    with open(data_file, 'rb') as f:
        files = {'files': ('分组误差柱形图数据.xlsx', f)}
        data = {
            'template_id': '多曲线/分组误差柱形图/main.py',
            'config': json.dumps(config)
        }
        response = requests.post(url, files=files, data=data)
        print(f'Status: {response.status_code}')
        if response.status_code != 200:
            print(f'Error: {response.text[:2000]}')
        else:
            output_file = f'test_output_{i}.png'
            with open(output_file, 'wb') as out:
                out.write(response.content)
            print(f'Saved to {output_file}')
