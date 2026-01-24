import os
import sys

# Paths to potential database files
db_files = [
    os.path.join("backend", "test.db"),
    os.path.join("backend", "app.db"),
    "test.db"
]

found = False
for db in db_files:
    if os.path.exists(db):
        try:
            os.remove(db)
            print(f"✅ Deleted database: {db}")
            found = True
        except Exception as e:
            print(f"❌ Failed to delete {db}: {e}")

if not found:
    print("⚠️ No database file found (it might be already clean).")

print("\n!!! IMPORTANT !!!")
print("Now restart the backend. It will re-scan 'main.py' from disk.")
