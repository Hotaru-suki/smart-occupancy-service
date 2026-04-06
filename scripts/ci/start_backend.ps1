param(
    [Parameter(Mandatory = $true)][string]$PythonExe,
    [string]$PidFile = "backend.pid",
    [string]$LogFile = "backend.log",
    [int]$StartupWaitSeconds = 5
)

$ErrorActionPreference = "Stop"

if (Test-Path $LogFile) {
    Remove-Item $LogFile -Force -ErrorAction SilentlyContinue
}

$process = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" `
    -RedirectStandardOutput $LogFile `
    -RedirectStandardError $LogFile `
    -PassThru

$process.Id | Out-File -FilePath $PidFile -Encoding ascii

Start-Sleep -Seconds $StartupWaitSeconds

$runningProcess = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
if (-not $runningProcess) {
    if (Test-Path $LogFile) {
        Get-Content $LogFile
    }
    exit 1
}
