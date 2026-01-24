$rootDir = "D:\文件夹\绘图"
Set-Location $rootDir
Start-Process cmd -ArgumentList "/c cd /d `"$rootDir\frontend`" && npm run dev" -WindowStyle Hidden
Start-Sleep -Seconds 3
Start-Process cmd -ArgumentList "/c cd /d `"$rootDir\backend`" && `"$rootDir\.venv\Scripts\activate.bat`" && set DATABASE_URL=sqlite:///$rootDir/test.db&& set TEMPLATES_ROOT=$rootDir/图像代码数据汇总&& uvicorn app.main:app --host 127.0.0.1 --port 8001" -WindowStyle Hidden
Start-Sleep -Seconds 10
Start-Process "http://localhost:5173"
