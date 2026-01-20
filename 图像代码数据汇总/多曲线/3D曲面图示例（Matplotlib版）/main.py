import matplotlib
matplotlib.use('Agg')  # 必须放在最前面，防止无界面环境报错
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
import glob
import os
import sys

# --- 1. 设置绘图风格与字体 (解决中文乱码) ---
plt.style.use('seaborn-v0_8-whitegrid') # 使用美观的样式
# 尝试多种常见中文字体
fonts = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans', 'SimSun']
for font in fonts:
    try:
        plt.rcParams['font.sans-serif'] = [font]
        # 验证字体是否有效
        fig_test = plt.figure()
        break
    except:
        continue
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

def load_data_smartly():
    """
    智能查找数据文件逻辑：
    1. 查找当前目录下所有的 xlsx, xls, csv 文件
    2. 优先排除名字里带 'demo' 或 '示范' 的文件（优先用用户上传的新数据）
    3. 如果只有示范数据，则使用示范数据
    """
    # 搜索文件
    extensions = ['*.xlsx', '*.xls', '*.csv']
    all_files = []
    for ext in extensions:
        all_files.extend(glob.glob(ext))
    
    if not all_files:
        # 打印当前目录内容，方便调试
        print(f"当前目录文件列表: {os.listdir('.')}")
        raise FileNotFoundError("未找到任何数据文件 (.xlsx, .xls, .csv)")
    
    # 筛选逻辑
    user_files = [f for f in all_files if "示范" not in f and "demo" not in f and "template" not in f]
    
    # 优先选中用户文件，否则选第一个文件
    target_file = user_files[0] if user_files else all_files[0]
    print(f"[系统提示] 正在读取文件: {target_file}")
    
    # 读取数据
    try:
        import matplotlib
        matplotlib.use('Agg') 
        import matplotlib.pyplot as plt
        import pandas as pd
        import numpy as np
        from mpl_toolkits.mplot3d import Axes3D
        import glob
        import os
        import sys

        # --- Settings ---
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False

        def load_data():
            """Smartly find and load any data file."""
            files = glob.glob('*.xlsx') + glob.glob('*.xls') + glob.glob('*.csv')
    
            if not files:
                print(f"DEBUG: Current directory files: {os.listdir('.')}")
                raise FileNotFoundError("No data files found! Please upload a .csv or .xlsx file.")
    
            target = files[0]
            for f in files:
                if "示范" not in f and "demo" not in f:
                    target = f
                    break
            
            print(f"[INFO] Loading file: {target}")
    
            if target.endswith('.csv'):
                try:
                    return pd.read_csv(target, encoding='utf-8')
                except Exception:
                    return pd.read_csv(target, encoding='gbk')
            else:
                return pd.read_excel(target)

        try:
            # 1. Load Data
            df = load_data()
    
            # 2. Data Cleaning
            df_numeric = df.select_dtypes(include=[np.number])
            if df_numeric.shape[1] < 3:
                raise ValueError(f"Data needs at least 3 numeric columns (x, y, z). Found: {df_numeric.columns.tolist()}")

            x = df_numeric.iloc[:, 0].values
            y = df_numeric.iloc[:, 1].values
            z = df_numeric.iloc[:, 2].values

            # 3. Plotting
            fig = plt.figure(figsize=(10, 8), dpi=120)
            ax = fig.add_subplot(111, projection='3d')

            surf = ax.plot_trisurf(x, y, z, cmap='viridis', edgecolor='none', alpha=0.8, antialiased=True)

            # 4. Decoration
            ax.set_title('3D Surface Plot', fontsize=14)
            ax.set_xlabel(df_numeric.columns[0])
            ax.set_ylabel(df_numeric.columns[1])
            ax.set_zlabel(df_numeric.columns[2])
    
            fig.colorbar(surf, ax=ax, shrink=0.6, aspect=10, label=df_numeric.columns[2])
            ax.view_init(elev=30, azim=-60)

            # 5. Save
            plt.tight_layout()
            plt.savefig('output.png')
            print("Success: output.png generated")

        except Exception as e:
            import traceback
            traceback.print_exc()
            sys.exit(1)