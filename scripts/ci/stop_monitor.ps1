param(
    [string]$PidFile = "monitor.pid",
    [string]$StopFlag = "monitor.stop",
    [int]$WaitSeconds = 10
)

$ErrorActionPreference = "SilentlyContinue"

New-Item -ItemType File -Path $StopFlag -Force | Out-Null

$monitorProcessId = $null
if (Test-Path $PidFile) {
    $monitorProcessId = Get-Content $PidFile | Select-Object -First 1
}

if ($monitorProcessId) {
    for ($i = 0; $i -lt $WaitSeconds; $i++) {
        $proc = Get-Process -Id $monitorProcessId -ErrorAction SilentlyContinue
        if (-not $proc) {
            break
        }
        Start-Sleep -Seconds 1
    }

    $proc = Get-Process -Id $monitorProcessId -ErrorAction SilentlyContinue
    if ($proc) {
        try { Stop-Process -Id $monitorProcessId -Force -ErrorAction SilentlyContinue } catch {}
    }
}

if (Test-Path $PidFile) {
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}
if (Test-Path $StopFlag) {
    Remove-Item $StopFlag -Force -ErrorAction SilentlyContinue
}