# 重新生成所有示范数据文件，确保格式与代码完全匹配
import pandas as pd
import numpy as np
import os

BASE_DIR = r"D:\文件夹\绘图\图像代码数据汇总"

def create_demo_data():
    """为每个模板创建正确格式的示范数据"""
    
    templates = {
        # 泰勒图 - 需要模型名、相关系数、标准差
        "泰勒图/泰勒图示例": {
            "columns": ["模型", "相关系数", "标准差"],
            "data": [
                ["XGBoost", 0.95, 1.05],
                ["FCN", 0.88, 1.15],
                ["LSTM", 0.92, 0.95],
                ["CNN-LSTM", 0.97, 1.02],
                ["Random Forest", 0.85, 1.20],
                ["SVR", 0.80, 1.30]
            ]
        },
        
        # 色标散点图 - x, y, 类别
        "色标散点图/边际组合图绘制示例": {
            "columns": ["X", "Y", "类别"],
            "data": lambda: generate_scatter_with_category()
        },
        
        # 散点对比图
        "散点对比图/模型预测对比图": {
            "columns": ["实测值", "预测值"],
            "data": lambda: generate_prediction_data(1)
        },
        "散点对比图/多模型预测效果对比": {
            "columns": ["实测值", "预测值_M1", "预测值_M2", "预测值_M3", "预测值_M4"],
            "data": lambda: generate_multi_model_prediction()
        },
        "散点对比图/三元相散点图绘制示例": {
            "columns": ["A", "B", "C", "Group"],
            "data": lambda: generate_ternary_data()
        },
        
        # 散点图
        "散点图/axes函数绘制子图示例": {
            "columns": ["X", "Y"],
            "data": lambda: generate_simple_scatter()
        },
        
        # 热力图
        "热力图/三元密度图": {
            "columns": ["A", "B", "C"],
            "data": lambda: generate_ternary_density_data()
        },
        
        # 柱状图
        "柱状图/图4-1-14 百分比堆积柱形图绘制示例": {
            "columns": ["类别", "系列1", "系列2", "系列3", "系列4"],
            "data": [
                ["类别A", 25, 30, 20, 25],
                ["类别B", 35, 25, 25, 15],
                ["类别C", 20, 35, 30, 15],
                ["类别D", 30, 20, 25, 25],
                ["类别E", 15, 40, 20, 25]
            ]
        },
        "柱状图/多类别相关性散点图": {
            "columns": ["X", "Y", "X_err", "Y_err", "类别"],
            "data": lambda: generate_error_scatter_data()
        },
        "柱状图/多子图相关性散点图（带Colorbar）": {
            "columns": ["X", "Y", "Z", "组别"],
            "data": lambda: generate_subplots_scatter_data()
        },
        "柱状图/矩阵气泡图": {
            "columns": ["行名", "列1", "列2", "列3", "列4", "列5"],
            "data": [
                ["行1", 85, 72, 91, 68, 77],
                ["行2", 63, 88, 75, 92, 81],
                ["行3", 79, 67, 84, 73, 96],
                ["行4", 91, 76, 62, 87, 69],
                ["行5", 74, 93, 78, 65, 82]
            ]
        },
        "柱状图/三元相气泡图": {
            "columns": ["A", "B", "C", "Size", "Color"],
            "data": lambda: generate_ternary_bubble_data()
        },
        "柱状图/颜色、散点大小映射的三元相散点图绘制示例": {
            "columns": ["A", "B", "C", "Color", "Size"],
            "data": lambda: generate_ternary_mapping_data()
        },
        
        # 多曲线
        "多曲线/3D曲面图示例（Matplotlib版）": {
            "columns": ["X", "Y", "Z"],
            "data": lambda: generate_3d_surface_data()
        },
        "多曲线/分组误差柱形图": {
            "columns": ["组别", "类型", "数值"],
            "data": lambda: generate_grouped_bar_data()
        },
        
        # 箱线图
        "箱线图/显著性标注箱线图": {
            "columns": ["组别", "数值"],
            "data": lambda: generate_boxplot_data()
        },
        
        # 小提琴图
        "小提琴图/小提琴图绘制示例": {
            "columns": ["组别", "数值"],
            "data": lambda: generate_violin_data()
        },
        "小提琴图/不同样式云雨图绘制示例": {
            "columns": ["组别", "数值"],
            "data": lambda: generate_raincloud_data()
        },
    }
    
    for template_path, config in templates.items():
        full_path = os.path.join(BASE_DIR, template_path, "示范数据.xlsx")
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        data = config["data"]
        if callable(data):
            data = data()
        
        df = pd.DataFrame(data, columns=config["columns"])
        df.to_excel(full_path, index=False)
        print(f"✓ 已生成: {template_path}/示范数据.xlsx")

# 数据生成函数
def generate_scatter_with_category():
    np.random.seed(42)
    data = []
    for cat in ['A类', 'B类', 'C类']:
        n = 50
        x = np.random.randn(n) * 2 + (ord(cat[0]) - 65) * 2
        y = x * 0.8 + np.random.randn(n)
        for i in range(n):
            data.append([x[i], y[i], cat])
    return data

def generate_prediction_data(model_count):
    np.random.seed(42)
    n = 50
    actual = np.random.uniform(10, 100, n)
    data = []
    for i in range(n):
        row = [actual[i], actual[i] + np.random.normal(0, 5)]
        data.append(row)
    return data

def generate_multi_model_prediction():
    np.random.seed(42)
    n = 50
    actual = np.random.uniform(10, 100, n)
    data = []
    for i in range(n):
        row = [
            actual[i],
            actual[i] + np.random.normal(0, 3),
            actual[i] + np.random.normal(0, 5),
            actual[i] + np.random.normal(0, 7),
            actual[i] + np.random.normal(0, 4)
        ]
        data.append(row)
    return data

def generate_ternary_data():
    np.random.seed(42)
    data = []
    for grp in ['组1', '组2', '组3']:
        for _ in range(20):
            a = np.random.uniform(0.2, 0.6)
            b = np.random.uniform(0.2, 0.6)
            c = 1 - a - b
            if c > 0:
                data.append([a, b, c, grp])
    return data

def generate_simple_scatter():
    np.random.seed(42)
    n = 100
    x = np.random.randn(n) * 3
    y = x * 0.7 + np.random.randn(n) * 2
    return [[x[i], y[i]] for i in range(n)]

def generate_ternary_density_data():
    np.random.seed(42)
    data = []
    centers = [(0.5, 0.3, 0.2), (0.3, 0.5, 0.2), (0.2, 0.3, 0.5)]
    for center in centers:
        for _ in range(100):
            a = np.random.normal(center[0], 0.1)
            b = np.random.normal(center[1], 0.1)
            c = np.random.normal(center[2], 0.1)
            a, b, c = abs(a), abs(b), abs(c)
            total = a + b + c
            data.append([a/total, b/total, c/total])
    return data

def generate_error_scatter_data():
    np.random.seed(42)
    data = []
    for cat in ['A类', 'B类', 'C类', 'D类']:
        n = 25
        idx = ord(cat[0]) - 65
        x = np.random.normal(idx * 2, 0.8, n)
        y = x * (0.8 + idx * 0.1) + np.random.normal(0, 0.5, n)
        x_err = np.random.uniform(0.1, 0.3, n)
        y_err = np.random.uniform(0.1, 0.4, n)
        for i in range(n):
            data.append([x[i], y[i], x_err[i], y_err[i], cat])
    return data

def generate_subplots_scatter_data():
    np.random.seed(42)
    data = []
    for grp in ['A', 'B', 'C', 'D']:
        n = 80
        idx = ord(grp) - 65
        x = np.random.randn(n) * (idx + 1)
        y = x * (0.5 + idx * 0.2) + np.random.randn(n) * 2
        z = np.abs(x * y) + np.random.rand(n) * 10
        for i in range(n):
            data.append([x[i], y[i], z[i], grp])
    return data

def generate_ternary_bubble_data():
    np.random.seed(42)
    data = []
    n = 30
    for _ in range(n):
        a = np.random.uniform(0.1, 0.8)
        b = np.random.uniform(0.1, 0.8)
        c = max(0.1, min(0.8, 1 - a - b))
        size = np.random.uniform(10, 50)
        color = np.random.uniform(0, 1)
        data.append([a, b, c, size, color])
    return data

def generate_ternary_mapping_data():
    np.random.seed(42)
    data = []
    n = 50
    for _ in range(n):
        a = np.random.uniform(0.1, 0.8)
        b = np.random.uniform(0.1, 0.8)
        c = max(0.1, min(0.8, 1 - a - b))
        color = a * b + np.random.uniform(0, 0.1)
        size = c * 300 + 50
        data.append([a, b, c, color, size])
    return data

def generate_3d_surface_data():
    x = np.linspace(-5, 5, 50)
    y = np.linspace(-5, 5, 50)
    X, Y = np.meshgrid(x, y)
    Z = np.sin(np.sqrt(X**2 + Y**2))
    data = []
    for i in range(len(x)):
        for j in range(len(y)):
            data.append([X[i, j], Y[i, j], Z[i, j]])
    return data

def generate_grouped_bar_data():
    data = []
    groups = ['Group A', 'Group B', 'Group C', 'Group D']
    types = ['Type 1', 'Type 2', 'Type 3']
    np.random.seed(42)
    for grp in groups:
        for typ in types:
            val = np.random.uniform(20, 100)
            data.append([grp, typ, val])
    return data

def generate_boxplot_data():
    np.random.seed(42)
    data = []
    for grp in ['Control', 'Treatment A', 'Treatment B', 'Treatment C']:
        n = 30
        base = np.random.uniform(50, 80)
        values = np.random.normal(base, 10, n)
        for v in values:
            data.append([grp, v])
    return data

def generate_violin_data():
    np.random.seed(42)
    data = []
    for grp in ['Group 1', 'Group 2', 'Group 3', 'Group 4']:
        n = 50
        base = np.random.uniform(40, 80)
        values = np.random.normal(base, 15, n)
        for v in values:
            data.append([grp, v])
    return data

def generate_raincloud_data():
    np.random.seed(42)
    data = []
    for grp in ['Condition A', 'Condition B', 'Condition C']:
        n = 40
        base = np.random.uniform(50, 90)
        values = np.random.normal(base, 12, n)
        for v in values:
            data.append([grp, v])
    return data

if __name__ == "__main__":
    print("开始重新生成所有示范数据...")
    create_demo_data()
    print("\n所有示范数据生成完成！")
