@echo off
echo Starting ECharts Lab...
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found
    pause
    exit /b 1
)

echo Starting frontend...
start /min cmd /c "cd /d %~dp0frontend && npm run dev"

timeout /t 2 /nobreak >nul

echo Starting backend...
set DATABASE_URL=sqlite:///%~dp0test.db
set TEMPLATES_ROOT=%~dp0图像代码数据汇总

start /min cmd /c "cd /d %~dp0backend && call %~dp0.venv\Scripts\activate.bat && uvicorn app.main:app --host 127.0.0.1 --port 8001"

echo.
echo Waiting for services to start...
timeout /t 8 /nobreak >nul

start "" http://localhost:5173

echo.
echo Services started!
echo   Frontend: http://localhost:5173
echo   Backend: http://localhost:8001
echo.
echo Services are running in minimized windows
echo To stop services, run stop.bat
echo.
pause
