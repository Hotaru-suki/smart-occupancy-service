$p = Start-Process -FilePath 'C:\Users\siest\Desktop\api\.venv\Scripts\python.exe' -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -PassThru
$p.Id | Out-File -FilePath 'backend.pid' -Encoding ascii
