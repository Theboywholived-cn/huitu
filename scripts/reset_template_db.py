#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置模板数据库（echarts_lab.db / app.db）
操作步骤：
  1. 备份原数据库文件
  2. 删除 templates 与 chart_types 表中的所有数据
  3. 打印重置后的行数确认
注意：仅清空数据，不删除表结构
"""
import os
import shutil
import sqlite3
from datetime import datetime

DB_PATHS = [
    r'C:\Users\31291\Desktop\软件项目管理实践\软件项目\huitu\backend\echarts_lab.db',
    r'C:\Users\31291\Desktop\软件项目管理实践\软件项目\huitu\backend\app.db',
]

TABLES_TO_CLEAR = ['templates', 'chart_types']

for db_path in DB_PATHS:
    if not os.path.exists(db_path):
        print(f'[跳过] 文件不存在: {db_path}')
        continue

    # 备份
    ts     = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = db_path + f'.bak_{ts}'
    shutil.copy2(db_path, backup)
    print(f'[备份] {os.path.basename(db_path)} → {os.path.basename(backup)}')

    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查询现有表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing = {row[0] for row in cursor.fetchall()}

    for table in TABLES_TO_CLEAR:
        if table in existing:
            cursor.execute(f'DELETE FROM {table}')
            print(f'  ✓ 已清空表 [{table}]，影响行数: {cursor.rowcount}')
        else:
            print(f'  - 表 [{table}] 不存在，跳过')

    conn.commit()
    conn.close()
    print(f'  完成: {os.path.basename(db_path)}\n')

print('全部数据库重置完毕。')
