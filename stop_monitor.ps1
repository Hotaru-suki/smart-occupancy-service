if (Test-Path 'monitor.pid') {
  $pid = Get-Content 'monitor.pid' | Select-Object -First 1
  if ($pid) { try { Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue } catch {} }
  Remove-Item 'monitor.pid' -Force -ErrorAction SilentlyContinue
}
