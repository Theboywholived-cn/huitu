@echo off
echo Stopping ECharts Lab services...
echo.

for /f "tokens=5" %%i in ('netstat -ano ^| findstr :5173') do (
    taskkill /F /PID %%i >nul 2>&1
    echo Frontend stopped
)

for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8001') do (
    taskkill /F /PID %%i >nul 2>&1
    echo Backend stopped
)

echo.
echo All services stopped
pause
