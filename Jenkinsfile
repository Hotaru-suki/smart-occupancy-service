def startMonitor(pyExe, keyword, label, outputFile, summaryFile) {
    bat """
    > start_monitor.ps1 echo \$p = Start-Process -FilePath '${pyExe}' -ArgumentList 'scripts\\\\monitor_resources.py','--interval','1','--keyword','${keyword}','--label','${label}','--output','${outputFile}','--summary-output','${summaryFile}' -PassThru
    >> start_monitor.ps1 echo \$p.Id ^| Out-File -FilePath 'monitor.pid' -Encoding ascii
    powershell -NoProfile -ExecutionPolicy Bypass -File start_monitor.ps1
    ping 127.0.0.1 -n 3 >nul
    """
}

def stopMonitor() {
    bat """
    if exist monitor.pid (
        for /f %%i in (monitor.pid) do taskkill /PID %%i /T /F >nul 2>nul
        del /f /q monitor.pid
    )
    """
}

def runLoadStage(scriptCtx, scenarioName, threads, ramp, loops, jmxFile, resultFile, reportDir) {
    def label = "${scenarioName}_${threads}"
    def monitorCsv = "monitoring\\\\${label}_resources.csv"

    scriptCtx.startMonitor(
        scriptCtx.env.PYTHON_EXE,
        scriptCtx.env.MONITOR_KEYWORD,
        label,
        monitorCsv,
        scriptCtx.env.MONITOR_SUMMARY
    )

    try {
        scriptCtx.bat """
        "${scriptCtx.env.JMETER_HOME}\\bin\\jmeter.bat" -n -t ${jmxFile} -Jthreads=${threads} -Jramp=${ramp} -Jloops=${loops} -l ${resultFile} -e -o ${reportDir}
        """
    } finally {
        scriptCtx.stopMonitor()
    }

    int breakerStatus = scriptCtx.bat(
        returnStatus: true,
        script: """
        "${scriptCtx.env.PYTHON_EXE}" scripts\\check_jmeter_breaker.py --jtl ${resultFile} --label ${label} --summary "${scriptCtx.env.BREAKER_SUMMARY}" --max-error-rate ${scriptCtx.env.BREAKER_MAX_ERROR_RATE} --max-p95-ms ${scriptCtx.env.BREAKER_MAX_P95_MS} --min-samples 20
        """
    )

    if (breakerStatus == 2) {
        scriptCtx.echo "Breaker triggered for ${label}, higher concurrency of same scenario will be skipped."
        return false
    }

    if (breakerStatus != 0) {
        scriptCtx.error("Breaker script failed for ${label}")
    }

    return true
}

pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        PROJECT_DIR              = 'C:\\Users\\siest\\Desktop\\api'
        PYTHON_EXE               = 'C:\\Users\\siest\\Desktop\\api\\.venv\\scripts\\python.exe'
        JMETER_HOME              = 'D:\\apache-jmeter-5.6.3\\apache-jmeter-5.6.3'
        ALLURE_RESULTS           = 'allure-results'

        APP_LOG                  = 'logs\\app.log'
        ERROR_LOG                = 'logs\\error.log'

        BACKEND_PID_FILE         = 'backend.pid'
        START_PS1                = 'start_backend.ps1'
        SMOKE_PS1                = 'smoke_check.ps1'
        KILL_PS1                 = 'kill_backend.ps1'

        ENV_FILE                 = '.env'
        ENV_TEST_FILE            = '.env.test'
        ENV_BACKUP_FILE          = '.env.bak'

        MONITOR_PID_FILE         = 'monitor.pid'
        MONITOR_PS1              = 'start_monitor.ps1'
        MONITOR_OUTPUT_DIR       = 'monitoring'
        MONITOR_SUMMARY          = 'monitoring\\monitor_summary.csv'
        MONITOR_KEYWORD          = 'uvicorn'

        BREAKER_SUMMARY          = 'monitoring\\breaker_summary.csv'
        BREAKER_MAX_ERROR_RATE   = '5'
        BREAKER_MAX_P95_MS       = '2000'

        PYTHONIOENCODING         = 'utf-8'
    }

    stages {
        stage('Precheck') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    if not exist "%PYTHON_EXE%" (
                        echo [ERROR] Python not found: %PYTHON_EXE%
                        exit /b 1
                    )

                    if not exist "requirements.txt" (
                        echo [ERROR] requirements.txt not found
                        exit /b 1
                    )

                    if not exist "%ENV_TEST_FILE%" (
                        echo [ERROR] %ENV_TEST_FILE% not found
                        exit /b 1
                    )

                    if not exist "app\\main.py" (
                        echo [ERROR] app\\main.py not found
                        exit /b 1
                    )

                    if not exist "tests" (
                        echo [ERROR] tests directory not found
                        exit /b 1
                    )

                    if not exist "docker-compose.yml" (
                        echo [ERROR] docker-compose.yml not found
                        exit /b 1
                    )

                    if not exist "jmeter\\health_baseline.jmx" (
                        echo [ERROR] jmeter\\health_baseline.jmx not found
                        exit /b 1
                    )

                    if not exist "jmeter\\status_load.jmx" (
                        echo [ERROR] jmeter\\status_load.jmx not found
                        exit /b 1
                    )

                    if not exist "jmeter\\page_polling_load.jmx" (
                        echo [ERROR] jmeter\\page_polling_load.jmx not found
                        exit /b 1
                    )

                    if not exist "scripts\\monitor_resources.py" (
                        echo [ERROR] scripts\\monitor_resources.py not found
                        exit /b 1
                    )

                    if not exist "scripts\\check_jmeter_breaker.py" (
                        echo [ERROR] scripts\\check_jmeter_breaker.py not found
                        exit /b 1
                    )

                    if not exist "%JMETER_HOME%\\bin\\jmeter.bat" (
                        echo [ERROR] JMeter not found: %JMETER_HOME%\\bin\\jmeter.bat
                        exit /b 1
                    )

                    docker info >nul 2>nul
                    if errorlevel 1 (
                        echo [ERROR] Docker Desktop is not running
                        exit /b 1
                    )

                    "%PYTHON_EXE%" --version
                    '''
                }
            }
        }

        stage('Prepare Env') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    if exist "%ENV_BACKUP_FILE%" del /f /q "%ENV_BACKUP_FILE%"
                    if exist "%ENV_FILE%" copy /Y "%ENV_FILE%" "%ENV_BACKUP_FILE%" >nul

                    copy /Y "%ENV_TEST_FILE%" "%ENV_FILE%"

                    if not exist logs mkdir logs
                    if not exist monitoring mkdir monitoring
                    '''
                }
            }
        }

        stage('Start Docker Services') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    docker compose up -d
                    '''
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%PYTHON_EXE%" -m pip install --upgrade pip
                    "%PYTHON_EXE%" -m pip install -r requirements.txt
                    '''
                }
            }
        }

        stage('Clean Old Results') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    if exist %ALLURE_RESULTS% rmdir /s /q %ALLURE_RESULTS%

                    if exist allure-report rmdir /s /q allure-report
                    if exist health-report rmdir /s /q health-report

                    if exist monitoring rmdir /s /q monitoring
                    mkdir monitoring

                    if exist status-report-20 rmdir /s /q status-report-20
                    if exist status-report-50 rmdir /s /q status-report-50
                    if exist status-report-100 rmdir /s /q status-report-100
                    if exist status-report-150 rmdir /s /q status-report-150
                    if exist status-report-200 rmdir /s /q status-report-200
                    if exist status-report-300 rmdir /s /q status-report-300

                    if exist polling-report-20 rmdir /s /q polling-report-20
                    if exist polling-report-50 rmdir /s /q polling-report-50
                    if exist polling-report-100 rmdir /s /q polling-report-100
                    if exist polling-report-150 rmdir /s /q polling-report-150
                    if exist polling-report-200 rmdir /s /q polling-report-200
                    if exist polling-report-300 rmdir /s /q polling-report-300

                    if exist health-result.jtl del /f /q health-result.jtl

                    if exist status-result-20.jtl del /f /q status-result-20.jtl
                    if exist status-result-50.jtl del /f /q status-result-50.jtl
                    if exist status-result-100.jtl del /f /q status-result-100.jtl
                    if exist status-result-150.jtl del /f /q status-result-150.jtl
                    if exist status-result-200.jtl del /f /q status-result-200.jtl
                    if exist status-result-300.jtl del /f /q status-result-300.jtl

                    if exist polling-result-20.jtl del /f /q polling-result-20.jtl
                    if exist polling-result-50.jtl del /f /q polling-result-50.jtl
                    if exist polling-result-100.jtl del /f /q polling-result-100.jtl
                    if exist polling-result-150.jtl del /f /q polling-result-150.jtl
                    if exist polling-result-200.jtl del /f /q polling-result-200.jtl
                    if exist polling-result-300.jtl del /f /q polling-result-300.jtl

                    if exist %BACKEND_PID_FILE% del /f /q %BACKEND_PID_FILE%
                    if exist %MONITOR_PID_FILE% del /f /q %MONITOR_PID_FILE%

                    if exist %START_PS1% del /f /q %START_PS1%
                    if exist %SMOKE_PS1% del /f /q %SMOKE_PS1%
                    if exist %KILL_PS1% del /f /q %KILL_PS1%
                    if exist %MONITOR_PS1% del /f /q %MONITOR_PS1%
                    '''
                }
            }
        }

        stage('Kill Old Backend On Port 8000') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    > %KILL_PS1% echo $conns = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
                    >> %KILL_PS1% echo if ($conns) {
                    >> %KILL_PS1% echo   foreach ($c in $conns) {
                    >> %KILL_PS1% echo     try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
                    >> %KILL_PS1% echo   }
                    >> %KILL_PS1% echo }

                    powershell -NoProfile -ExecutionPolicy Bypass -File %KILL_PS1%
                    '''
                }
            }
        }

        stage('Start Backend') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    > %START_PS1% echo $p = Start-Process -FilePath '%PYTHON_EXE%' -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -PassThru
                    >> %START_PS1% echo $p.Id ^| Out-File -FilePath '%BACKEND_PID_FILE%' -Encoding ascii

                    powershell -NoProfile -ExecutionPolicy Bypass -File %START_PS1%
                    ping 127.0.0.1 -n 6 >nul
                    '''
                }
            }
        }

        stage('Smoke Check') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    > %SMOKE_PS1% echo $ok = $false
                    >> %SMOKE_PS1% echo for ($i = 0; $i -lt 10; $i++) {
                    >> %SMOKE_PS1% echo   try {
                    >> %SMOKE_PS1% echo     $resp = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/' -UseBasicParsing -TimeoutSec 5
                    >> %SMOKE_PS1% echo     Write-Host ('status=' + $resp.StatusCode)
                    >> %SMOKE_PS1% echo     if ($resp.StatusCode -eq 200) { $ok = $true; break }
                    >> %SMOKE_PS1% echo   } catch {
                    >> %SMOKE_PS1% echo     Write-Host $_.Exception.Message
                    >> %SMOKE_PS1% echo   }
                    >> %SMOKE_PS1% echo   Start-Sleep -Seconds 2
                    >> %SMOKE_PS1% echo }
                    >> %SMOKE_PS1% echo if (-not $ok) { exit 1 }

                    powershell -NoProfile -ExecutionPolicy Bypass -File %SMOKE_PS1%
                    '''
                }
            }
        }

        stage('Run Pytest') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%PYTHON_EXE%" -m pytest tests --alluredir=%ALLURE_RESULTS%
                    '''
                }
            }
        }

        stage('Run JMeter - Health Baseline') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\health_baseline.jmx -Jthreads=5 -Jramp=5 -Jloops=10 -l health-result.jtl -e -o health-report
                    '''
                }
            }
        }

        stage('Run Status Load Ladder') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    script {
                        def continueStatus = true

                        if (continueStatus) {
                            continueStatus = runLoadStage(this, "status", 20, 5, 40, "jmeter\\status_load.jmx", "status-result-20.jtl", "status-report-20")
                        }
                        if (continueStatus) {
                            continueStatus = runLoadStage(this, "status", 50, 10, 40, "jmeter\\status_load.jmx", "status-result-50.jtl", "status-report-50")
                        }
                        if (continueStatus) {
                            continueStatus = runLoadStage(this, "status", 100, 20, 40, "jmeter\\status_load.jmx", "status-result-100.jtl", "status-report-100")
                        }
                        if (continueStatus) {
                            continueStatus = runLoadStage(this, "status", 150, 30, 40, "jmeter\\status_load.jmx", "status-result-150.jtl", "status-report-150")
                        }
                        if (continueStatus) {
                            continueStatus = runLoadStage(this, "status", 200, 40, 40, "jmeter\\status_load.jmx", "status-result-200.jtl", "status-report-200")
                        }
                        if (continueStatus) {
                            continueStatus = runLoadStage(this, "status", 300, 60, 40, "jmeter\\status_load.jmx", "status-result-300.jtl", "status-report-300")
                        }

                        if (!continueStatus) {
                            echo 'Status load ladder stopped by breaker.'
                        }
                    }
                }
            }
        }

        stage('Run Polling Load Ladder') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    script {
                        def continuePolling = true

                        if (continuePolling) {
                            continuePolling = runLoadStage(this, "polling", 20, 5, 40, "jmeter\\page_polling_load.jmx", "polling-result-20.jtl", "polling-report-20")
                        }
                        if (continuePolling) {
                            continuePolling = runLoadStage(this, "polling", 50, 10, 40, "jmeter\\page_polling_load.jmx", "polling-result-50.jtl", "polling-report-50")
                        }
                        if (continuePolling) {
                            continuePolling = runLoadStage(this, "polling", 100, 20, 40, "jmeter\\page_polling_load.jmx", "polling-result-100.jtl", "polling-report-100")
                        }
                        if (continuePolling) {
                            continuePolling = runLoadStage(this, "polling", 150, 30, 40, "jmeter\\page_polling_load.jmx", "polling-result-150.jtl", "polling-report-150")
                        }
                        if (continuePolling) {
                            continuePolling = runLoadStage(this, "polling", 200, 40, 40, "jmeter\\page_polling_load.jmx", "polling-result-200.jtl", "polling-report-200")
                        }
                        if (continuePolling) {
                            continuePolling = runLoadStage(this, "polling", 300, 60, 40, "jmeter\\page_polling_load.jmx", "polling-result-300.jtl", "polling-report-300")
                        }

                        if (!continuePolling) {
                            echo 'Polling load ladder stopped by breaker.'
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            dir("${env.PROJECT_DIR}") {
                script {
                    stopMonitor()

                    if (fileExists(env.BACKEND_PID_FILE)) {
                        bat '''
                        for /f %%i in (%BACKEND_PID_FILE%) do taskkill /PID %%i /T /F >nul 2>nul
                        '''
                    } else {
                        bat '''
                        > %KILL_PS1% echo $conns = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
                        >> %KILL_PS1% echo if ($conns) {
                        >> %KILL_PS1% echo   foreach ($c in $conns) {
                        >> %KILL_PS1% echo     try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction SilentlyContinue } catch {}
                        >> %KILL_PS1% echo   }
                        >> %KILL_PS1% echo }
                        powershell -NoProfile -ExecutionPolicy Bypass -File %KILL_PS1%
                        '''
                    }
                }

                archiveArtifacts artifacts: 'logs/app.log', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'logs/error.log', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'allure-results/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'health-report/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'status-report-*/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'polling-report-*/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: '*-result-*.jtl', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'health-result.jtl', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'monitoring/**', fingerprint: true, allowEmptyArchive: true

                allure([
                    includeProperties: false,
                    jdk: '',
                    results: [[path: 'allure-results']]
                ])

                bat '''
                if exist "%ENV_FILE%" del /f /q "%ENV_FILE%"
                if exist "%ENV_BACKUP_FILE%" ren "%ENV_BACKUP_FILE%" "%ENV_FILE%"

                if exist %BACKEND_PID_FILE% del /f /q %BACKEND_PID_FILE%
                if exist %MONITOR_PID_FILE% del /f /q %MONITOR_PID_FILE%
                if exist %START_PS1% del /f /q %START_PS1%
                if exist %SMOKE_PS1% del /f /q %SMOKE_PS1%
                if exist %KILL_PS1% del /f /q %KILL_PS1%
                if exist %MONITOR_PS1% del /f /q %MONITOR_PS1%
                '''
            }
        }

        success {
            echo 'Pipeline succeeded.'
        }

        failure {
            echo 'Pipeline failed. Check console output, logs/app.log, logs/error.log and monitoring artifacts.'
        }
    }
}