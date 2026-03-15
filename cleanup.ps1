$ErrorActionPreference = 'SilentlyContinue'
if (Test-Path 'allure-results') { Remove-Item 'allure-results' -Recurse -Force }
if (Test-Path 'allure-report') { Remove-Item 'allure-report' -Recurse -Force }
if (Test-Path 'health-report') { Remove-Item 'health-report' -Recurse -Force }
Get-ChildItem -Path . -Directory -Filter 'status-report-*' | ForEach-Object { Remove-Item $_.FullName -Recurse -Force }
Get-ChildItem -Path . -Directory -Filter 'polling-report-*' | ForEach-Object { Remove-Item $_.FullName -Recurse -Force }
if (Test-Path 'monitoring') { Remove-Item 'monitoring' -Recurse -Force }
New-Item -ItemType Directory -Path 'monitoring' -Force | Out-Null
if (Test-Path 'health-result.jtl') { Remove-Item 'health-result.jtl' -Force }
Get-ChildItem -Path . -File -Filter 'status-result-*.jtl' | ForEach-Object { Remove-Item $_.FullName -Force }
Get-ChildItem -Path . -File -Filter 'polling-result-*.jtl' | ForEach-Object { Remove-Item $_.FullName -Force }
if (Test-Path 'backend.pid') { Remove-Item 'backend.pid' -Force }
if (Test-Path 'monitor.pid') { Remove-Item 'monitor.pid' -Force }
if (Test-Path 'start_backend.ps1') { Remove-Item 'start_backend.ps1' -Force }
if (Test-Path 'smoke_check.ps1') { Remove-Item 'smoke_check.ps1' -Force }
if (Test-Path 'kill_backend.ps1') { Remove-Item 'kill_backend.ps1' -Force }
if (Test-Path 'start_monitor.ps1') { Remove-Item 'start_monitor.ps1' -Force }
if (Test-Path 'stop_monitor.ps1') { Remove-Item 'stop_monitor.ps1' -Force }
if (Test-Path 'pre_jmeter_cleanup.ps1') { Remove-Item 'pre_jmeter_cleanup.ps1' -Force }
