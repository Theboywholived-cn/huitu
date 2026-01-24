# ECharts Lab 停止脚本
# 停止前端和后端服务

Write-Host "正在停止 ECharts Lab 服务..." -ForegroundColor Yellow

# 停止前端 (node/npm)
$frontendProcesses = Get-Process -Name "node" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*vite*" -or $_.MainWindowTitle -like "*vite*"
}

if ($frontendProcesses) {
    $frontendProcesses | ForEach-Object {
        Stop-Process -Id $_.Id -Force
        Write-Host "  ✓ 已停止前端进程 (PID: $($_.Id))" -ForegroundColor Green
    }
} else {
    # 尝试通过端口查找
    $connection = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
    if ($connection) {
        $pid = $connection.OwningProcess
        Stop-Process -Id $pid -Force
        Write-Host "  ✓ 已停止前端进程 (PID: $pid)" -ForegroundColor Green
    } else {
        Write-Host "  - 前端服务未运行" -ForegroundColor Gray
    }
}

# 停止后端 (Python/uvicorn)
$backendProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -like "*uvicorn*" -or $_.CommandLine -like "*app.main:app*"
}

if ($backendProcesses) {
    $backendProcesses | ForEach-Object {
        Stop-Process -Id $_.Id -Force
        Write-Host "  ✓ 已停止后端进程 (PID: $($_.Id))" -ForegroundColor Green
    }
} else {
    # 尝试通过端口查找
    $connection = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
    if ($connection) {
        $pid = $connection.OwningProcess
        Stop-Process -Id $pid -Force
        Write-Host "  ✓ 已停止后端进程 (PID: $pid)" -ForegroundColor Green
    } else {
        Write-Host "  - 后端服务未运行" -ForegroundColor Gray
    }
}

# 停止所有相关的 cmd 进程
$cmdProcesses = Get-Process -Name "cmd" -ErrorAction SilentlyContinue
foreach ($proc in $cmdProcesses) {
    try {
        $commandLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
        if ($commandLine -like "*npm*" -or $commandLine -like "*uvicorn*") {
            Stop-Process -Id $proc.Id -Force
            Write-Host "  ✓ 已停止 CMD 进程 (PID: $($proc.Id))" -ForegroundColor Green
        }
    } catch {
        # 忽略错误
    }
}

Write-Host "`n✓ 所有服务已停止" -ForegroundColor Green
