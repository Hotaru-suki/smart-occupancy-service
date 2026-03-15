$ok = $false
for ($i = 0; $i -lt 15; $i++) {
  try {
    $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/' -UseBasicParsing -TimeoutSec 5
    Write-Host ('status=' + $resp.StatusCode)
    if ($resp.StatusCode -eq 200) { $ok = $true; break }
  } catch {
    Write-Host $_.Exception.Message
  }
  Start-Sleep -Seconds 2
}
if (-not $ok) { exit 1 }
