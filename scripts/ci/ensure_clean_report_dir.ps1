param(
    [Parameter(Mandatory = $true)][string]$ReportDir
)

$ErrorActionPreference = "SilentlyContinue"

if (Test-Path $ReportDir) {
    Remove-Item $ReportDir -Recurse -Force
}