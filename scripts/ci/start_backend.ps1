param(
    [Parameter(Mandatory = $true)][string]$PythonExe,
    [string]$PidFile = "backend.pid",
    [string]$StdoutLogFile = "backend.stdout.log",
    [string]$StderrLogFile = "backend.stderr.log",
    [int]$StartupWaitSeconds = 5
)

$ErrorActionPreference = "Stop"

if (Test-Path $StdoutLogFile) {
    Remove-Item $StdoutLogFile -Force -ErrorAction SilentlyContinue
}
if (Test-Path $StderrLogFile) {
    Remove-Item $StderrLogFile -Force -ErrorAction SilentlyContinue
}

$process = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" `
    -RedirectStandardOutput $StdoutLogFile `
    -RedirectStandardError $StderrLogFile `
    -PassThru

$process.Id | Out-File -FilePath $PidFile -Encoding ascii

Start-Sleep -Seconds $StartupWaitSeconds

$runningProcess = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
if (-not $runningProcess) {
    if (Test-Path $StdoutLogFile) {
        Get-Content $StdoutLogFile
    }
    if (Test-Path $StderrLogFile) {
        Get-Content $StderrLogFile
    }
    exit 1
}
