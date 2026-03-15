param(
    [string]$AllureResults = "allure-results",
    [string]$BackendPidFile = "backend.pid",
    [string]$MonitorPidFile = "monitor.pid"
)

$ErrorActionPreference = "SilentlyContinue"

if (Test-Path $AllureResults) { Remove-Item $AllureResults -Recurse -Force }
if (Test-Path "allure-report") { Remove-Item "allure-report" -Recurse -Force }
if (Test-Path "health-report") { Remove-Item "health-report" -Recurse -Force }

Get-ChildItem -Path . -Directory -Filter "status-report-*" | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
}
Get-ChildItem -Path . -Directory -Filter "polling-report-*" | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force
}

if (Test-Path "monitoring") { Remove-Item "monitoring" -Recurse -Force }
New-Item -ItemType Directory -Path "monitoring" -Force | Out-Null

Get-ChildItem -Path . -File -Filter "status-result-*.jtl" | ForEach-Object {
    Remove-Item $_.FullName -Force
}
Get-ChildItem -Path . -File -Filter "polling-result-*.jtl" | ForEach-Object {
    Remove-Item $_.FullName -Force
}

if (Test-Path "health-result.jtl") { Remove-Item "health-result.jtl" -Force }

if (Test-Path $BackendPidFile) { Remove-Item $BackendPidFile -Force }
if (Test-Path $MonitorPidFile) { Remove-Item $MonitorPidFile -Force }