# ECharts Lab 启动脚本
# 此脚本会在后台启动前端和后端服务

Write-Host "正在启动 ECharts Lab..." -ForegroundColor Green

# 设置工作目录
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $rootDir

# 检查虚拟环境
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "错误: 未找到虚拟环境，请先运行 python -m venv .venv 创建虚拟环境" -ForegroundColor Red
    exit 1
}

# 检查端口占用
$frontendPort = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
$backendPort = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue

if ($frontendPort) {
    Write-Host "前端端口 5173 已被占用，跳过启动" -ForegroundColor Yellow
} else {
    Write-Host "启动前端服务..." -ForegroundColor Cyan
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd `"$rootDir\frontend`" && npm run dev" -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

if ($backendPort) {
    Write-Host "后端端口 8001 已被占用，跳过启动" -ForegroundColor Yellow
} else {
    Write-Host "启动后端服务..." -ForegroundColor Cyan
    $env:DATABASE_URL = "sqlite:///$rootDir/test.db"
    $env:TEMPLATES_ROOT = "$rootDir/图像代码数据汇总"
    
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd `"$rootDir\backend`" && `"$rootDir\.venv\Scripts\activate.bat`" && uvicorn app.main:app --host 127.0.0.1 --port 8001" -WindowStyle Hidden
    Start-Sleep -Seconds 3
}

# 等待服务启动
Write-Host "等待服务启动..." -ForegroundColor Cyan
Start-Sleep -Seconds 5

# 检查服务状态
$frontendRunning = Get-NetTCPConnection -LocalPort 5173 -State Listen -ErrorAction SilentlyContinue
$backendRunning = Get-NetTCPConnection -LocalPort 8001 -State Listen -ErrorAction SilentlyContinue

Write-Host "`n服务状态:" -ForegroundColor Green
if ($frontendRunning) {
    Write-Host "  ✓ 前端: http://localhost:5173" -ForegroundColor Green
} else {
    Write-Host "  ✗ 前端: 启动失败" -ForegroundColor Red
}

if ($backendRunning) {
    Write-Host "  ✓ 后端: http://localhost:8001" -ForegroundColor Green
} else {
    Write-Host "  ✗ 后端: 启动失败" -ForegroundColor Red
}

if ($frontendRunning -and $backendRunning) {
    Write-Host "`n✓ 所有服务已启动，请在浏览器中访问 http://localhost:5173" -ForegroundColor Green
    Write-Host "提示: 服务在后台运行，关闭此窗口不会停止服务" -ForegroundColor Yellow
    Write-Host "要停止服务，请运行 .\stop.ps1" -ForegroundColor Yellow
    
    # 可选: 自动打开浏览器
    # Start-Process "http://localhost:5173"
} else {
    Write-Host "`n⚠ 部分服务启动失败，请检查日志" -ForegroundColor Yellow
}
