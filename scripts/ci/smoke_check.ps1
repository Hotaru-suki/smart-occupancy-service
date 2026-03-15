param(
    [string]$Url = "http://127.0.0.1:8000/",
    [int]$MaxRetry = 15,
    [int]$SleepSeconds = 2
)

$ok = $false

for ($i = 0; $i -lt $MaxRetry; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        Write-Host ("status=" + $resp.StatusCode)
        if ($resp.StatusCode -eq 200) {
            $ok = $true
            break
        }
    } catch {
        Write-Host $_.Exception.Message
    }
    Start-Sleep -Seconds $SleepSeconds
}

if (-not $ok) {
    exit 1
}