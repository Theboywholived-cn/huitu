#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成折线图/多曲线图的示例数据"""
import pandas as pd
import numpy as np

np.random.seed(0)

months = [f'{m}月' for m in range(1, 13)]

df = pd.DataFrame({
    '月份':   months,
    '产品A': np.round(np.cumsum(np.random.randn(12)) + 50, 2).tolist(),
    '产品B': np.round(np.cumsum(np.random.randn(12)) + 60, 2).tolist(),
    '产品C': np.round(np.cumsum(np.random.randn(12)) + 45, 2).tolist(),
    '产品D': np.round(np.cumsum(np.random.randn(12)) + 55, 2).tolist(),
})

output_path = r'D:\文件夹\绘图\图像代码数据汇总\折线图\多曲线折线图\示范数据.xlsx'
df.to_excel(output_path, index=False)
print(f'已生成: {output_path}')
print(f'共 {len(df)} 行，{len(df.columns)-1} 条曲线')
