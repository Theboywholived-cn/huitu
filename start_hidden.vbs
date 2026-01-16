Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")













































[System.Windows.Forms.MessageBox]::Show("服务已在后台启动！`n`n前端: http://localhost:5173`n后端: http://localhost:8001`n`n如果无法访问，请稍等片刻。`n要停止服务，请运行 stop.bat", "ECharts Lab", 0, 64)Add-Type -AssemblyName System.Windows.Forms# 显示提示Start-Process "http://localhost:5173"# 打开浏览器Start-Sleep -Seconds 10Start-Process cmd -ArgumentList "/c `"$env:TEMP\echarts_backend.bat`"" -WindowStyle Hidden# 启动后端（完全隐藏）Start-Sleep -Seconds 3Start-Process cmd -ArgumentList "/c `"$env:TEMP\echarts_frontend.bat`"" -WindowStyle Hidden# 启动前端（完全隐藏）$backendScript | Out-File -FilePath "$env:TEMP\echarts_backend.bat" -Encoding ASCII$frontendScript | Out-File -FilePath "$env:TEMP\echarts_frontend.bat" -Encoding ASCII# 保存临时脚本"@uvicorn app.main:app --host 127.0.0.1 --port 8001set TEMPLATES_ROOT=$rootDir/图像代码数据汇总set DATABASE_URL=sqlite:///$rootDir/test.dbcall "$rootDir\.venv\Scripts\activate.bat"cd /d "$rootDir\backend"$backendScript = @""@npm run devcd /d "$rootDir\frontend"$frontendScript = @"# 创建启动脚本文件}    exit 1    [System.Windows.Forms.MessageBox]::Show("未找到虚拟环境！", "启动失败", 0, 16)if (-not (Test-Path ".venv\Scripts\python.exe")) {# 检查虚拟环境Set-Location $rootDir$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
' 获取脚本所在目录
scriptPath = FSO.GetParentFolderName(WScript.ScriptFullName)

' 检查虚拟环境
If Not FSO.FileExists(scriptPath & "\.venv\Scripts\python.exe") Then
    MsgBox "错误: 未找到虚拟环境" & vbCrLf & scriptPath & "\.venv\Scripts\python.exe", 16, "启动失败"
    WScript.Quit
End If

' 启动前端 (完全隐藏，不等待)
frontendCmd = "cmd /c cd /d """ & scriptPath & "\frontend"" && npm run dev"
WshShell.Run frontendCmd, 0, False

' 等待 3 秒
WScript.Sleep 3000

' 启动后端 (完全隐藏，不等待)
backendCmd = "cmd /c cd /d """ & scriptPath & "\backend"" && """ & scriptPath & "\.venv\Scripts\activate.bat"" && set ""DATABASE_URL=sqlite:///" & scriptPath & "/test.db"" && set ""TEMPLATES_ROOT=" & scriptPath & "\图像代码数据汇总"" && uvicorn app.main:app --host 127.0.0.1 --port 8001"
WshShell.Run backendCmd, 0, False

' 等待 12 秒让服务启动
WScript.Sleep 12000

' 打开浏览器
WshShell.Run "http://localhost:5173", 1, False

MsgBox "服务已在后台启动！" & vbCrLf & vbCrLf & "前端: http://localhost:5173" & vbCrLf & "后端: http://localhost:8001" & vbCrLf & vbCrLf & "如果无法访问，请稍等片刻让服务完全启动。" & vbCrLf & vbCrLf & "要停止服务，请运行 stop.bat", 64, "ECharts Lab"
