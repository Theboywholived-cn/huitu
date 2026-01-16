import matplotlib
matplotlib.use('Agg') # 必须在最前面
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import os
import glob
import sys

# 设置中文字体（避免乱码，可选）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def find_data_file():
    """智能查找数据文件：优先查找用户上传的新文件"""
    # 查找所有 Excel 和 CSV
    all_files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    
    if not all_files:
        raise FileNotFoundError("当前目录下没有找到任何 .xlsx 或 .csv 数据文件！")
    
    # 策略：优先使用不包含 "示范" 或 "demo" 字样的文件
    # 因为用户上传的文件名通常不同于默认文件名
    user_files = [f for f in all_files if "示范" not in f and "demo" not in f]
    
    if user_files:
        print(f"检测到用户上传文件，使用: {user_files[0]}")
        return user_files[0]
    else:
        print(f"未检测到自定义文件，使用默认文件: {all_files[0]}")
        return all_files[0]

try:
    # 1. 加载数据
    data_file = find_data_file()
    if data_file.endswith('.csv'):
        df = pd.read_csv(data_file)
    else:
        df = pd.read_excel(data_file)

    # 清洗数据：只保留数值列
    df = df.select_dtypes(include=[np.number])
    
    # 检查列数
    if df.shape[1] < 3:
        raise ValueError(f"数据列数不足！需要至尝3列(x,y,z)，当前文件只有: {df.columns.tolist()}")

    # 2. 绘图设置
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')

    # 3. 提取数据 (强制取前三列)
    x = df.iloc[:, 0].values
    y = df.iloc[:, 1].values
    z = df.iloc[:, 2].values

    # 4. 绘制三角剖分曲面 (適应性最强，不需要网格数据)
    # cmap 推荐: viridis, plasma, coolwarm, magma
    surf = ax.plot_trisurf(x, y, z, cmap='viridis', edgecolor='none', alpha=0.9, linewidth=0.1, antialiased=True)

    # 5. 装饰图表
    ax.set_xlabel(df.columns[0], fontsize=10)
    ax.set_ylabel(df.columns[1], fontsize=10)
    ax.set_zlabel(df.columns[2], fontsize=10)
    ax.set_title(f'3D Surface: {data_file}', fontsize=12)

    # 添加颜色条
    cbar = fig.colorbar(surf, ax=ax, shrink=0.6, aspect=12, pad=0.1)
    cbar.set_label(df.columns[2])

    # 调整视角 (什角　30度，方位角-60度)
    ax.view_init(elev=30, azim=-60)

    # 6. 保存图片
    plt.tight_layout()
    save_path = 'output.png'
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"图像生成成功: {save_path}")

except Exception as e:
    # 将错误打印到标准输出，以便前端捕获
    print(f"Error: {str(e)}")
    sys.exit(1)
