import sqlite3
import os

db_path = r'D:\文件夹\绘图\backend\echarts_lab.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查找包含 Colorbar 或 多子图相关性 的模板
cursor.execute("SELECT id, name FROM templates WHERE name LIKE '%Colorbar%' OR name LIKE '%多子图相关性%'")
results = cursor.fetchall()

if results:
    print("找到以下模板:")
    for r in results:
        print(f"  ID: {r[0]}, Name: {r[1]}")
    
    # 删除这些模板
    for r in results:
        cursor.execute("DELETE FROM templates WHERE id = ?", (r[0],))
        print(f"  已删除: {r[1]}")
    
    conn.commit()
    print("删除完成")
else:
    print("没有找到相关模板记录")

conn.close()
