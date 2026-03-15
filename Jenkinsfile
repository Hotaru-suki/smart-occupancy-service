pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        PROJECT_DIR        = 'C:\\Users\\siest\\Desktop\\api'
        PYTHON_EXE         = 'C:\\Users\\siest\\Desktop\\api\\.venv\\Scripts\\python.exe'
        JMETER_HOME        = 'D:\\apache-jmeter-5.6.3\\apache-jmeter-5.6.3'
        ALLURE_RESULTS     = 'allure-results'

        APP_LOG            = 'logs\\app.log'
        ERROR_LOG          = 'logs\\error.log'

        BACKEND_PID_FILE   = 'backend.pid'
        START_PS1          = 'start_backend.ps1'
        SMOKE_PS1          = 'smoke_check.ps1'
        KILL_PS1           = 'kill_backend.ps1'

        ENV_FILE           = '.env'
        ENV_TEST_FILE      = '.env.test'
        ENV_BACKUP_FILE    = '.env.bak'

        PYTHONIOENCODING   = 'utf-8'
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
                    if exist status-report rmdir /s /q status-report
                    if exist polling-report rmdir /s /q polling-report

                    if exist status-report-10 rmdir /s /q status-report-10
                    if exist status-report-30 rmdir /s /q status-report-30
                    if exist status-report-50 rmdir /s /q status-report-50
                    if exist status-report-80 rmdir /s /q status-report-80
                    if exist status-report-100 rmdir /s /q status-report-100

                    if exist polling-report-10 rmdir /s /q polling-report-10
                    if exist polling-report-30 rmdir /s /q polling-report-30
                    if exist polling-report-50 rmdir /s /q polling-report-50
                    if exist polling-report-80 rmdir /s /q polling-report-80
                    if exist polling-report-100 rmdir /s /q polling-report-100

                    if exist health-result.jtl del /f /q health-result.jtl
                    if exist status-result.jtl del /f /q status-result.jtl
                    if exist polling-result.jtl del /f /q polling-result.jtl

                    if exist status-result-10.jtl del /f /q status-result-10.jtl
                    if exist status-result-30.jtl del /f /q status-result-30.jtl
                    if exist status-result-50.jtl del /f /q status-result-50.jtl
                    if exist status-result-80.jtl del /f /q status-result-80.jtl
                    if exist status-result-100.jtl del /f /q status-result-100.jtl

                    if exist polling-result-10.jtl del /f /q polling-result-10.jtl
                    if exist polling-result-30.jtl del /f /q polling-result-30.jtl
                    if exist polling-result-50.jtl del /f /q polling-result-50.jtl
                    if exist polling-result-80.jtl del /f /q polling-result-80.jtl
                    if exist polling-result-100.jtl del /f /q polling-result-100.jtl

                    if exist %BACKEND_PID_FILE% del /f /q %BACKEND_PID_FILE%

                    if exist %START_PS1% del /f /q %START_PS1%
                    if exist %SMOKE_PS1% del /f /q %SMOKE_PS1%
                    if exist %KILL_PS1% del /f /q %KILL_PS1%
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

        stage('Run JMeter - Status Load 10') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\status_load.jmx -Jthreads=10 -Jramp=5 -Jloops=30 -l status-result-10.jtl -e -o status-report-10
                    '''
                }
            }
        }

        stage('Run JMeter - Status Load 30') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\status_load.jmx -Jthreads=30 -Jramp=10 -Jloops=30 -l status-result-30.jtl -e -o status-report-30
                    '''
                }
            }
        }

        stage('Run JMeter - Status Load 50') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\status_load.jmx -Jthreads=50 -Jramp=15 -Jloops=30 -l status-result-50.jtl -e -o status-report-50
                    '''
                }
            }
        }

        stage('Run JMeter - Status Load 80') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\status_load.jmx -Jthreads=80 -Jramp=20 -Jloops=30 -l status-result-80.jtl -e -o status-report-80
                    '''
                }
            }
        }

        stage('Run JMeter - Status Load 100') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\status_load.jmx -Jthreads=100 -Jramp=25 -Jloops=30 -l status-result-100.jtl -e -o status-report-100
                    '''
                }
            }
        }

        stage('Run JMeter - Polling Load 10') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\page_polling_load.jmx -Jthreads=10 -Jramp=5 -Jloops=30 -l polling-result-10.jtl -e -o polling-report-10
                    '''
                }
            }
        }

        stage('Run JMeter - Polling Load 30') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\page_polling_load.jmx -Jthreads=30 -Jramp=10 -Jloops=30 -l polling-result-30.jtl -e -o polling-report-30
                    '''
                }
            }
        }

        stage('Run JMeter - Polling Load 50') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\page_polling_load.jmx -Jthreads=50 -Jramp=15 -Jloops=30 -l polling-result-50.jtl -e -o polling-report-50
                    '''
                }
            }
        }

        stage('Run JMeter - Polling Load 80') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\page_polling_load.jmx -Jthreads=80 -Jramp=20 -Jloops=30 -l polling-result-80.jtl -e -o polling-report-80
                    '''
                }
            }
        }

        stage('Run JMeter - Polling Load 100') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\page_polling_load.jmx -Jthreads=100 -Jramp=25 -Jloops=30 -l polling-result-100.jtl -e -o polling-report-100
                    '''
                }
            }
        }
    }

    post {
        always {
            dir("${env.PROJECT_DIR}") {
                script {
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
                archiveArtifacts artifacts: '*.jtl', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: '*-report/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'status-report-*/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'polling-report-*/**', fingerprint: true, allowEmptyArchive: true

                allure([
                    includeProperties: false,
                    jdk: '',
                    results: [[path: 'allure-results']]
                ])

                bat '''
                if exist "%ENV_FILE%" del /f /q "%ENV_FILE%"
                if exist "%ENV_BACKUP_FILE%" ren "%ENV_BACKUP_FILE%" "%ENV_FILE%"

                if exist %BACKEND_PID_FILE% del /f /q %BACKEND_PID_FILE%
                if exist %START_PS1% del /f /q %START_PS1%
                if exist %SMOKE_PS1% del /f /q %SMOKE_PS1%
                if exist %KILL_PS1% del /f /q %KILL_PS1%
                '''
            }
        }

        success {
            echo 'Pipeline succeeded.'
        }

        failure {
            echo 'Pipeline failed. Check console output, logs/app.log and logs/error.log.'
        }
    }
}