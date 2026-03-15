param(
    [Parameter(Mandatory = $true)][string]$PythonExe,
    [Parameter(Mandatory = $true)][string]$Keyword,
    [Parameter(Mandatory = $true)][string]$Label,
    [Parameter(Mandatory = $true)][string]$OutputFile,
    [Parameter(Mandatory = $true)][string]$SummaryFile,
    [string]$PidFile = "monitor.pid",
    [string]$StopFlag = "monitor.stop"
)

if (Test-Path $StopFlag) {
    Remove-Item $StopFlag -Force -ErrorAction SilentlyContinue
}

$process = Start-Process -FilePath $PythonExe `
    -ArgumentList "scripts\monitor_resources.py","--interval","1","--keyword",$Keyword,"--label",$Label,"--output",$OutputFile,"--summary-output",$SummaryFile,"--stop-flag",$StopFlag `
    -PassThru

$process.Id | Out-File -FilePath $PidFile -Encoding ascii