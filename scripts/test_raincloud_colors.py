#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试云雨图配色方案"""
import requests
import json

url = 'http://127.0.0.1:8000/api/templates/run-configured'
data_file = r'D:\文件夹\绘图\图像代码数据汇总\小提琴图\不同样式云雨图绘制示例\示范数据.xlsx'

# 测试不同配色方案
colormaps = ['jet', 'viridis', 'plasma', 'coolwarm', 'RdYlBu', 'hot']

for cm in colormaps:
    config = {
        'colormap': cm,
        'raincloud_style': 1,
        'fig_width': 8,
        'fig_height': 6,
        'dpi': 150
    }
    
    with open(data_file, 'rb') as f:
        files = {'files': ('示范数据.xlsx', f)}
        data = {
            'template_id': '小提琴图/不同样式云雨图绘制示例/main.py',
            'config': json.dumps(config)
        }
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            output_file = f'test_raincloud_{cm}.png'
            with open(output_file, 'wb') as out:
                out.write(response.content)
            print(f'✓ {cm}: Saved ({len(response.content)} bytes)')
        else:
            print(f'✗ {cm}: Error - {response.text[:200]}')
