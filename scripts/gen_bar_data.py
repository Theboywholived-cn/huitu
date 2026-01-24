#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成通用柱状图的示例数据"""
import pandas as pd

df = pd.DataFrame({
    '类别': ['A', 'B', 'C', 'D', 'E'],
    '数值1': [23, 45, 32, 67, 54],
    '数值2': [31, 38, 42, 59, 48],
    '数值3': [28, 51, 35, 62, 43],
})

output_path = r'D:\文件夹\绘图\图像代码数据汇总\柱状图\通用柱状图\示范数据.xlsx'
df.to_excel(output_path, index=False)
print(f'已生成: {output_path}')
