param(
    [Parameter(Mandatory = $true)][string]$PythonExe,
    [string]$PidFile = "backend.pid"
)

$process = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" `
    -PassThru

$process.Id | Out-File -FilePath $PidFile -Encoding ascii