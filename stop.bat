@echo off
chcp 65001 >nul 2>&1
title Stop ECharts Lab
echo ========================================
echo   Stopping ECharts Lab services...
echo ========================================
echo.

:: Stop by port 8000 (backend)
echo [1/2] Stopping Backend (port 8000)...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    taskkill /F /PID %%i >nul 2>&1
)
echo      Backend stopped.

:: Stop by port 5173 (frontend)
echo [2/2] Stopping Frontend (port 5173)...
for /f "tokens=5" %%i in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    taskkill /F /PID %%i >nul 2>&1
)
echo      Frontend stopped.

:: Also kill any remaining python/node processes from this project (optional but thorough)
taskkill /F /IM "node.exe" /FI "WINDOWTITLE eq ECharts*" >nul 2>&1
taskkill /F /IM "python.exe" /FI "WINDOWTITLE eq ECharts*" >nul 2>&1

echo.
echo ========================================
echo   All services stopped successfully!
echo ========================================
echo.
pause
