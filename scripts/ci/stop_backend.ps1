param(
    [int]$Port = 8000,
    [string]$PidFile = "backend.pid"
)

$ErrorActionPreference = "SilentlyContinue"

if (Test-Path $PidFile) {
    $backendProcessId = Get-Content $PidFile | Select-Object -First 1
    if ($backendProcessId) {
        try { Stop-Process -Id $backendProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

$conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($conns) {
    foreach ($conn in $conns) {
        try { Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
    }
}