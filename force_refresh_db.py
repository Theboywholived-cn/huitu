import os

db_path = os.path.join("backend", "test.db")

if os.path.exists(db_path):
    print(f"Removing old database: {db_path}")
    os.remove(db_path)
    print("Database removed. Please restart the backend to trigger a fresh scan of the template files.")
else:
    print("Database file not found (it might have been already cleared).")
