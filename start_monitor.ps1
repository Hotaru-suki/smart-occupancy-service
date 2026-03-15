$p = Start-Process -FilePath 'C:\Users\siest\Desktop\api\.venv\Scripts\python.exe' -ArgumentList 'scripts\\monitor_resources.py','--interval','1','--keyword','uvicorn','--label','status_50','--output','monitoring\\status_50_resources.csv','--summary-output','monitoring\monitor_summary.csv' -PassThru
$p.Id | Out-File -FilePath 'monitor.pid' -Encoding ascii
