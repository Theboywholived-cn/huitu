#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为每个模板目录生成可选取的测试数据（示范数据.xlsx）。
仅在目录内没有现有 .xlsx/.xls/.csv 时创建。
"""
import os
import random

import pandas as pd

TEMPLATES_ROOT = r"D:\文件夹\绘图\图像代码数据汇总"


def _has_data_files(folder: str) -> bool:
    for name in os.listdir(folder):
        if name.lower().endswith((".xlsx", ".xls", ".csv")):
            return True
    return False


def _read_code_text(folder: str) -> str:
    # 优先 main.py，否则读取任意 .py
    main_path = os.path.join(folder, "main.py")
    if os.path.exists(main_path):
        try:
            with open(main_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        except Exception:
            return ""
    for name in os.listdir(folder):
        if name.endswith(".py"):
            try:
                with open(os.path.join(folder, name), "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception:
                continue
    return ""


def _make_demo_df(code_text: str, folder_name: str) -> pd.DataFrame:
    text = (code_text + " " + folder_name).lower()

    # 泰勒图
    if "taylor" in text or "泰勒" in text:
        return pd.DataFrame({
            "Model": ["M1", "M2", "M3", "M4"],
            "STD": [0.8, 0.9, 1.1, 1.2],
            "CORR": [0.72, 0.81, 0.88, 0.93],
            "RMSE": [0.45, 0.38, 0.30, 0.25]
        })

    # 三元相/三元图
    if "ternary" in text or "三元" in text:
        rows = []
        for i in range(12):
            a = random.uniform(10, 80)
            b = random.uniform(5, 80 - a)
            c = 100 - a - b
            rows.append({"A": round(a, 2), "B": round(b, 2), "C": round(c, 2), "Group": f"G{i%3+1}"})
        return pd.DataFrame(rows)

    # 箱线图/小提琴
    if any(k in text for k in ["box", "箱线", "violin", "小提琴", "云雨"]):
        rows = []
        for g in ["A", "B", "C"]:
            for _ in range(30):
                rows.append({"Group": g, "Value": round(random.gauss(50 + 5*ord(g)%7, 8), 2)})
        return pd.DataFrame(rows)

    # 热力图/密度图
    if any(k in text for k in ["heatmap", "密度", "热力"]):
        rows = []
        for x in range(1, 6):
            for y in range(1, 6):
                rows.append({"X": x, "Y": y, "Value": round(random.uniform(0, 1), 3)})
        return pd.DataFrame(rows)

    # 柱状图
    if any(k in text for k in ["bar", "柱"]):
        return pd.DataFrame({
            "Category": ["A", "B", "C", "D"],
            "Value": [12, 18, 9, 15],
            "Series": ["S1", "S1", "S1", "S1"]
        })

    # 折线/多曲线
    if any(k in text for k in ["plot", "line", "曲线", "折线"]):
        return pd.DataFrame({
            "X": list(range(1, 11)),
            "Y1": [2, 3, 4, 6, 5, 7, 8, 7, 9, 10],
            "Y2": [1, 2, 2, 3, 4, 5, 5, 6, 7, 8]
        })

    # 散点图（含色标）
    if any(k in text for k in ["scatter", "散点"]):
        rows = []
        for i in range(50):
            x = random.uniform(0, 100)
            y = x * 0.8 + random.uniform(-10, 10)
            rows.append({"X": round(x, 2), "Y": round(y, 2), "Value": round(random.uniform(0, 1), 3)})
        return pd.DataFrame(rows)

    # 默认通用
    return pd.DataFrame({
        "X": list(range(1, 11)),
        "Y": [random.uniform(0, 10) for _ in range(10)]
    })


def main() -> None:
    created = 0
    skipped = 0
    
    for root, dirs, files in os.walk(TEMPLATES_ROOT):
        if ".idea" in root:
            continue
        if "main.py" in files:
            if _has_data_files(root):
                skipped += 1
                continue
            code_text = _read_code_text(root)
            df = _make_demo_df(code_text, os.path.basename(root))
            out_path = os.path.join(root, "示范数据.xlsx")
            try:
                df.to_excel(out_path, index=False)
                created += 1
                print(f"✓ 创建: {out_path}")
            except Exception as e:
                print(f"✗ 失败: {out_path} -> {e}")
    
    print(f"\n完成: 创建 {created} 个，跳过 {skipped} 个。")


if __name__ == "__main__":
    main()
