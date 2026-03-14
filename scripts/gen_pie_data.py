#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成饼图/环形图的示例数据"""
import pandas as pd

df = pd.DataFrame({
    '类别': ['电子产品', '服装鞋帽', '食品饮料', '家居用品', '运动户外', '其他'],
    '销售额': [3820, 2560, 4710, 1890, 2240, 980],
    '占比': [24.5, 16.4, 30.2, 12.1, 14.4, 6.3],
})

output_path = r'D:\文件夹\绘图\图像代码数据汇总\饼图\通用饼图\示范数据.xlsx'
df.to_excel(output_path, index=False)
print(f'已生成: {output_path}')
print(f'共 {len(df)} 个类别，总销售额: {df["销售额"].sum()}')
