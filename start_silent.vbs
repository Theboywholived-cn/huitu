Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Get current directory of the script
rootPath = fso.GetParentFolderName(WScript.ScriptFullName)

' Paths
venvPython = rootPath & "\.venv\Scripts\python.exe"
backendDir = rootPath & "\backend"
frontendDir = rootPath & "\frontend"

' Quote helper
Function Q(s)
    Q = Chr(34) & s & Chr(34)
End Function

' 2. Start Backend using venv python directly (more reliable than activate.bat)
cmdBackend = "cmd /c cd /d " & Q(backendDir) & " && " & Q(venvPython) & " -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
WshShell.Run cmdBackend, 0, False

' 3. Start Frontend (runs in background, no window)
cmdFrontend = "cmd /c cd /d " & Q(frontendDir) & " && npm run dev"
WshShell.Run cmdFrontend, 0, False

' 4. Wait for services to initialize and open browser
WScript.Sleep 5000
WshShell.Run "http://localhost:5173"

' Notification
MsgBox "ECharts Lab started!" & vbCrLf & vbCrLf & _
       "Backend: http://127.0.0.1:8000" & vbCrLf & _
       "Frontend: http://localhost:5173" & vbCrLf & vbCrLf & _
       "To stop: use Task Manager to end node.exe and python.exe", _
       64, "ECharts Lab"