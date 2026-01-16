# 利用Mayavi绘制的其他3D曲面图示例
# 注意：运行此代码需要安装mayavi库：pip install mayavi
# 如果无法安装mayavi，可以使用matplotlib的3D功能替代

import os
import numpy as np
import pandas as pd

try:
    from mayavi import mlab
    USE_MAYAVI = True
except ImportError:
    USE_MAYAVI = False
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D

# 设置中文字体（仅matplotlib需要）
if not USE_MAYAVI:
    plt.rcParams['font.sans-serif'] = ['SimHei', 'WenQuanYi Zen Hei', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

def _find_data_file() -> str | None:
    # 优先示范数据
    if os.path.exists('示范数据.xlsx'):
        return '示范数据.xlsx'
    for name in os.listdir('.'):
        if name.lower().endswith(('.xlsx', '.xls', '.csv')):
            return name
    return None


def _load_surface_data() -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    file_name = _find_data_file()
    if not file_name:
        return None
    try:
        if file_name.lower().endswith('.csv'):
            df = pd.read_csv(file_name)
        else:
            df = pd.read_excel(file_name)
    except Exception:
        return None

    # 标准列名优先：X, Y, Z / Value
    cols = {c.lower(): c for c in df.columns}
    x_col = cols.get('x')
    y_col = cols.get('y')
    z_col = cols.get('z') or cols.get('value')
    if not (x_col and y_col and z_col):
        return None

    try:
        pivot = df.pivot_table(index=y_col, columns=x_col, values=z_col, aggfunc='mean')
        x_vals = pivot.columns.values.astype(float)
        y_vals = pivot.index.values.astype(float)
        X, Y = np.meshgrid(x_vals, y_vals)
        Z = pivot.values.astype(float)
        return X, Y, Z
    except Exception:
        return None


surface_data = _load_surface_data()

if USE_MAYAVI:
    # 使用Mayavi绘制
    # 1. 球面
    phi, theta = np.mgrid[0:2*np.pi:100j, 0:np.pi:50j]
    x1 = np.sin(theta) * np.cos(phi)
    y1 = np.sin(theta) * np.sin(phi)
    z1 = np.cos(theta)
    
    mlab.figure(size=(800, 600), bgcolor=(1, 1, 1))
    mlab.mesh(x1, y1, z1, scalars=z1, colormap='viridis')
    mlab.title('Mayavi 3D Sphere')
    
    # 2. 波浪曲面
    x2, y2 = np.mgrid[-5:5:100j, -5:5:100j]
    z2 = np.sin(np.sqrt(x2**2 + y2**2))
    
    mlab.figure(size=(800, 600), bgcolor=(1, 1, 1))
    mlab.surf(x2, y2, z2, colormap='coolwarm')
    mlab.title('Mayavi Wave Surface')
    
    mlab.show()
else:
    # 使用Matplotlib替代
    if surface_data is not None:
        # 数据驱动：单个曲面
        X, Y, Z = surface_data
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(1, 1, 1, projection='3d')
        surf = ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.9)
        fig.colorbar(surf, shrink=0.6, aspect=12)
        ax.set_title('3D曲面图示例（Matplotlib版）', fontsize=14)
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        plt.tight_layout()
        plt.show()
    else:
        fig = plt.figure(figsize=(16, 12))
        
        # 1. 球面
        ax1 = fig.add_subplot(2, 2, 1, projection='3d')
        u = np.linspace(0, 2 * np.pi, 50)
        v = np.linspace(0, np.pi, 30)
        x1 = np.outer(np.cos(u), np.sin(v))
        y1 = np.outer(np.sin(u), np.sin(v))
        z1 = np.outer(np.ones(np.size(u)), np.cos(v))
        ax1.plot_surface(x1, y1, z1, cmap='viridis', alpha=0.8)
        ax1.set_title('球面', fontsize=12)
        
        # 2. 波浪曲面
        ax2 = fig.add_subplot(2, 2, 2, projection='3d')
        x2 = np.linspace(-5, 5, 50)
        y2 = np.linspace(-5, 5, 50)
        X2, Y2 = np.meshgrid(x2, y2)
        Z2 = np.sin(np.sqrt(X2**2 + Y2**2))
        ax2.plot_surface(X2, Y2, Z2, cmap='coolwarm', alpha=0.8)
        ax2.set_title('波浪曲面', fontsize=12)
        
        # 3. 马鞍面
        ax3 = fig.add_subplot(2, 2, 3, projection='3d')
        x3 = np.linspace(-2, 2, 50)
        y3 = np.linspace(-2, 2, 50)
        X3, Y3 = np.meshgrid(x3, y3)
        Z3 = X3**2 - Y3**2
        ax3.plot_surface(X3, Y3, Z3, cmap='plasma', alpha=0.8)
        ax3.set_title('马鞍面', fontsize=12)
        
        # 4. 圆环面
        ax4 = fig.add_subplot(2, 2, 4, projection='3d')
        u4 = np.linspace(0, 2 * np.pi, 50)
        v4 = np.linspace(0, 2 * np.pi, 50)
        U4, V4 = np.meshgrid(u4, v4)
        R, r = 2, 0.5
        X4 = (R + r * np.cos(V4)) * np.cos(U4)
        Y4 = (R + r * np.cos(V4)) * np.sin(U4)
        Z4 = r * np.sin(V4)
        ax4.plot_surface(X4, Y4, Z4, cmap='RdYlBu', alpha=0.8)
        ax4.set_title('圆环面', fontsize=12)
        
        plt.suptitle('3D曲面图示例（Matplotlib版）', fontsize=14)
        plt.tight_layout()
        plt.show()
