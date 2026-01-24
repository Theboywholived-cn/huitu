import pandas as pd
import numpy as np

np.random.seed(42)
data1 = np.random.rand(100, 100)
data2 = np.random.rand(100, 100)

with pd.ExcelWriter('子图数据.xlsx') as writer:
    pd.DataFrame(data1).to_excel(writer, sheet_name='Sheet1', index=False)
    pd.DataFrame(data2).to_excel(writer, sheet_name='Sheet2', index=False)

print('子图数据.xlsx 已生成')
