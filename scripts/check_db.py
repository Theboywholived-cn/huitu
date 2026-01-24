import sqlite3
import sys

conn = sqlite3.connect('test.db')
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f"数据库中的表: {[t[0] for t in tables]}")

# 如果有 users 表，检查用户数量
if any('users' in str(t) for t in tables):
    cursor.execute("SELECT COUNT(*) FROM users")
    print(f"用户数量: {cursor.fetchone()[0]}")

conn.close()
