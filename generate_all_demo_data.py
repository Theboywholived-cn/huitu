#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为每个模板生成正确格式的示范数据，并确保数据格式与代码兼容。
同时更新代码使其能读取外部数据。
"""
import os
import numpy as np
import pandas as pd

TEMPLATES_ROOT = r"D:\文件夹\绘图\图像代码数据汇总"

def generate_demo_data():
    """为每个模板生成适配的示范数据"""
    
    templates = {
        # (路径, 生成函数)
        "多曲线/分组误差柱形图": gen_grouped_bar_data,
        "小提琴图/不同样式云雨图绘制示例": gen_violin_data,
        "小提琴图/小提琴图绘制示例": gen_violin_data,
        "散点图/axes函数绘制子图示例": gen_scatter_data,
        "散点对比图/多模型预测效果对比": gen_model_comparison_data,
        "散点对比图/模型预测对比图": gen_model_comparison_data,
        "散点对比图/三元相散点图绘制示例": gen_ternary_data,
        "柱状图/多类别相关性散点图": gen_category_scatter_data,
        "柱状图/多子图相关性散点图（带Colorbar）": gen_multi_scatter_data,
        "柱状图/矩阵气泡图": gen_matrix_bubble_data,
        "柱状图/三元相气泡图": gen_ternary_data,
        "柱状图/图4-1-14 百分比堆积柱形图绘制示例": gen_stacked_bar_data,
        "柱状图/颜色、散点大小映射的三元相散点图绘制示例": gen_ternary_data,
        "热力图/三元密度图": gen_ternary_data,
        "箱线图/显著性标注箱线图": gen_boxplot_data,
        "色标散点图/边际组合图绘制示例": gen_marginal_scatter_data,
    }
    
    for rel_path, gen_func in templates.items():
        full_path = os.path.join(TEMPLATES_ROOT, rel_path)
        if not os.path.exists(full_path):
            print(f"⚠ 目录不存在: {rel_path}")
            continue
        
        out_file = os.path.join(full_path, "示范数据.xlsx")
        try:
            df = gen_func()
            df.to_excel(out_file, index=False)
            print(f"✓ {rel_path}")
        except Exception as e:
            print(f"✗ {rel_path}: {e}")


def gen_grouped_bar_data():
    """分组误差柱形图: 组别, 类型, 数值"""
    np.random.seed(42)
    n = 20
    return pd.DataFrame({
        '组别': np.repeat(['组A', '组B', '组C'], n),
        '类型': np.tile(np.repeat(['类型1', '类型2'], n//2), 3),
        '数值': np.concatenate([
            np.random.normal(50, 10, n),
            np.random.normal(60, 12, n),
            np.random.normal(55, 8, n),
        ])
    })


def gen_violin_data():
    """小提琴图/云雨图: 组别, 数值"""
    np.random.seed(42)
    n = 50
    return pd.DataFrame({
        '组别': np.repeat(['组A', '组B', '组C', '组D'], n),
        '数值': np.concatenate([
            np.random.normal(50, 10, n),
            np.random.normal(60, 15, n),
            np.concatenate([np.random.normal(40, 5, n//2), np.random.normal(70, 5, n//2)]),
            np.random.exponential(10, n) + 30,
        ])
    })


def gen_scatter_data():
    """散点图: X, Y"""
    np.random.seed(42)
    n = 50
    x = np.random.uniform(0, 10, n)
    y = x * 0.8 + np.random.normal(0, 1, n)
    return pd.DataFrame({'X': x, 'Y': y})


def gen_model_comparison_data():
    """模型对比散点图: 实测值, 预测值_M1, 预测值_M2, ..."""
    np.random.seed(42)
    n = 50
    actual = np.linspace(0, 100, n) + np.random.normal(0, 5, n)
    return pd.DataFrame({
        '实测值': actual,
        '预测值_M1': actual * 0.9 + np.random.normal(0, 8, n),
        '预测值_M2': actual * 1.05 + np.random.normal(0, 6, n),
        '预测值_M3': actual * 0.95 + np.random.normal(0, 4, n),
        '预测值_M4': actual * 1.0 + np.random.normal(0, 3, n),
    })


def gen_ternary_data():
    """三元图: A, B, C (和为100)"""
    np.random.seed(42)
    n = 30
    rows = []
    for i in range(n):
        a = np.random.uniform(10, 70)
        b = np.random.uniform(10, min(70, 100 - a - 10))
        c = 100 - a - b
        rows.append({'A': round(a, 2), 'B': round(b, 2), 'C': round(c, 2), 'Group': f'G{i%3+1}'})
    return pd.DataFrame(rows)


def gen_category_scatter_data():
    """分类散点图: X, Y, 类别"""
    np.random.seed(42)
    n = 100
    categories = ['类别A', '类别B', '类别C']
    data = []
    for i, cat in enumerate(categories):
        x = np.random.normal(i * 2, 1, n // 3)
        y = x * 0.5 + np.random.normal(i, 0.5, n // 3)
        for xi, yi in zip(x, y):
            data.append({'X': xi, 'Y': yi, '类别': cat})
    return pd.DataFrame(data)


def gen_multi_scatter_data():
    """多子图散点图: X, Y, Value"""
    np.random.seed(42)
    n = 100
    x = np.random.uniform(0, 100, n)
    y = x * 0.8 + np.random.normal(0, 10, n)
    value = np.random.uniform(0, 1, n)
    return pd.DataFrame({'X': x, 'Y': y, 'Value': value})


def gen_matrix_bubble_data():
    """矩阵气泡图: Row, Col, Value"""
    rows = []
    labels = ['A', 'B', 'C', 'D', 'E']
    np.random.seed(42)
    for r in labels:
        for c in labels:
            rows.append({'Row': r, 'Col': c, 'Value': round(np.random.uniform(0, 1), 3)})
    return pd.DataFrame(rows)


def gen_stacked_bar_data():
    """百分比堆积柱形图: 类别, 系列1, 系列2, ..."""
    return pd.DataFrame({
        '类别': ['A', 'B', 'C', 'D'],
        '系列1': [20, 35, 30, 35],
        '系列2': [25, 32, 34, 20],
        '系列3': [30, 20, 15, 25],
        '系列4': [25, 13, 21, 20],
    })


def gen_boxplot_data():
    """箱线图: 组别, 数值"""
    np.random.seed(42)
    n = 30
    return pd.DataFrame({
        '组别': np.repeat(['对照组', '实验组A', '实验组B', '实验组C'], n),
        '数值': np.concatenate([
            np.random.normal(50, 8, n),
            np.random.normal(60, 10, n),
            np.random.normal(55, 7, n),
            np.random.normal(70, 9, n),
        ])
    })


def gen_marginal_scatter_data():
    """边际组合图: X, Y, 类别"""
    np.random.seed(42)
    n = 150
    categories = ['类别1', '类别2', '类别3']
    data = []
    for i, cat in enumerate(categories):
        x = np.random.normal(5 + i * 2, 1.5, n // 3)
        y = np.random.normal(5 + i * 1.5, 1.2, n // 3)
        for xi, yi in zip(x, y):
            data.append({'X': xi, 'Y': yi, '类别': cat})
    return pd.DataFrame(data)


if __name__ == "__main__":
    print("🔄 生成示范数据...")
    generate_demo_data()
    print("\n✓ 完成!")
