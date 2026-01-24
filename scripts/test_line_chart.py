#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试折线图配色方案"""
import requests
import json

url = 'http://127.0.0.1:8000/api/templates/run-configured'
data_file = r'D:\文件夹\绘图\图像代码数据汇总\多曲线\通用折线图\折线图数据.xlsx'

# 测试不同配色方案
colormaps = ['jet', 'Set1', 'Set2', 'Paired', 'viridis', 'plasma']

for cm in colormaps:
    config = {
        'colormap': cm,
        'marker_style': 'o',
        'line_style': '-',
        'line_width': 2,
        'marker_size': 8,
        'fig_width': 10,
        'fig_height': 7,
        'dpi': 150
    }
    
    with open(data_file, 'rb') as f:
        files = {'files': ('折线图数据.xlsx', f)}
        data = {
            'template_id': '多曲线/通用折线图/main.py',
            'config': json.dumps(config)
        }
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            output_file = f'test_line_{cm}.png'
            with open(output_file, 'wb') as out:
                out.write(response.content)
            print(f'✓ {cm}: Saved to {output_file}')
        else:
            print(f'✗ {cm}: Error - {response.text[:200]}')
