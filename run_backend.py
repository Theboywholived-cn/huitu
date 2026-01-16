import os
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["TEMPLATES_ROOT"] = "D:/文件夹/绘图/图像代码数据汇总"
os.chdir(r"D:\文件夹\绘图\backend")
import uvicorn
uvicorn.run("app.main:app", host="127.0.0.1", port=8001, log_level="info")
