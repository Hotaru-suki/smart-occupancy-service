param(
    [Parameter(Mandatory = $true)][string]$Host,
    [Parameter(Mandatory = $true)][int]$Port,
    [int]$MaxRetry = 30,
    [int]$SleepSeconds = 2
)

$ErrorActionPreference = "SilentlyContinue"
$ready = $false

for ($i = 0; $i -lt $MaxRetry; $i++) {
    $tcpClient = $null
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $async = $tcpClient.BeginConnect($Host, $Port, $null, $null)
        $connected = $async.AsyncWaitHandle.WaitOne(2000, $false)
        if ($connected -and $tcpClient.Connected) {
            $tcpClient.EndConnect($async)
            Write-Host "ready ${Host}:${Port}"
            $ready = $true
            break
        }
    } catch {
        Write-Host $_.Exception.Message
    } finally {
        if ($tcpClient) {
            $tcpClient.Close()
        }
    }

    Start-Sleep -Seconds $SleepSeconds
}

if (-not $ready) {
    exit 1
}
