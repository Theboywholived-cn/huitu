@echo off
echo Starting ECharts Lab (hidden mode)...
powershell -ExecutionPolicy Bypass -Command "cd '%~dp0'; Start-Process cmd -ArgumentList '/c cd /d \"%~dp0frontend\" && npm run dev' -WindowStyle Hidden; Start-Sleep -Seconds 3; Start-Process cmd -ArgumentList '/c cd /d \"%~dp0backend\" && \"%~dp0.venv\Scripts\activate.bat\" && set DATABASE_URL=sqlite:///%~dp0test.db&& set TEMPLATES_ROOT=%~dp0图像代码数据汇总&& uvicorn app.main:app --host 127.0.0.1 --port 8001' -WindowStyle Hidden; Start-Sleep -Seconds 10; Start-Process 'http://localhost:5173'"
echo.
echo Services started in background!
echo Frontend: http://localhost:5173
echo Backend: http://localhost:8001
echo.
echo Browser will open automatically.
echo To stop services, run stop.bat
echo.
pause
