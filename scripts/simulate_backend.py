#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""模拟后端执行过程"""
import os
import sys
import shutil
import tempfile
import subprocess

# 模拟的配置代码
config_code = '''
# ========== Chart Configuration (Auto-generated) ==========
import json as _json

class ChartConfig:
    x_column = None
    y_columns = None
    group_column = None
    selected_pairs = None
    
    marker_style = "o"
    marker_size = 50
    line_style = "-"
    line_width = 2
    
    colors = None
    colormap = "Set1"
    
    title = "分组误差柱形图"
    x_label = ""
    y_label = ""
    show_legend = True
    show_grid = True
    
    fig_width = 10.0
    fig_height = 8.0
    dpi = 150
    
    # 柱形图专属配置
    show_points = True
    show_error = True
    error_type = "sd"
    bar_width = 0.8
    point_size = 5

# Make config available as global
CHART_CONFIG = ChartConfig()
# ========== End Configuration ==========

'''

# 路径
template_path = r"D:\文件夹\绘图\图像代码数据汇总\多曲线\分组误差柱形图\main.py"
data_path = r"D:\文件夹\绘图\图像代码数据汇总\多曲线\分组误差柱形图\分组误差柱形图数据.xlsx"

# 创建临时目录
with tempfile.TemporaryDirectory(prefix="test_") as tmpdir:
    print(f"临时目录: {tmpdir}")
    
    # 读取原始main.py
    with open(template_path, 'r', encoding='utf-8') as f:
        original_code = f.read()
    
    # 合并配置代码
    modified_code = config_code + original_code
    
    # 写入修改后的main.py
    main_file = os.path.join(tmpdir, 'main.py')
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(modified_code)
    
    print(f"写入 main.py: {len(modified_code)} 字符")
    
    # 复制数据文件
    shutil.copy2(data_path, os.path.join(tmpdir, '分组误差柱形图数据.xlsx'))
    print("复制数据文件")
    
    # 设置环境
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["MPLCONFIGDIR"] = tmpdir
    env["PYTHONUTF8"] = "1"
    
    # 执行
    print("开始执行...")
    proc = subprocess.run(
        [sys.executable, "main.py"],
        cwd=tmpdir,
        env=env,
        capture_output=True,
        timeout=60,
        encoding='utf-8',
        errors='replace'
    )
    
    print(f"\n返回码: {proc.returncode}")
    print(f"\n标准输出:\n{proc.stdout}")
    print(f"\n标准错误:\n{proc.stderr}")
    
    # 检查输出
    output_png = os.path.join(tmpdir, 'output.png')
    if os.path.exists(output_png):
        print(f"\n成功! 输出文件大小: {os.path.getsize(output_png)} bytes")
    else:
        print("\n失败! 没有生成 output.png")
        print(f"目录内容: {os.listdir(tmpdir)}")
