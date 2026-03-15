def runPs(scriptCtx, file, args = '') {
    scriptCtx.bat """
    powershell -NoProfile -ExecutionPolicy Bypass -File "${file}" ${args}
    """
}

def startMonitor(scriptCtx, label) {
    runPs(
        scriptCtx,
        'scripts\\ci\\start_monitor.ps1',
        "-PythonExe \"${scriptCtx.env.PYTHON_EXE}\" -Keyword \"${scriptCtx.env.MONITOR_KEYWORD}\" -Label \"${label}\" -OutputFile \"monitoring\\${label}_resources.csv\" -SummaryFile \"${scriptCtx.env.MONITOR_SUMMARY}\" -PidFile \"${scriptCtx.env.MONITOR_PID_FILE}\" -StopFlag \"${scriptCtx.env.MONITOR_STOP_FLAG}\""
    )
}

def stopMonitor(scriptCtx) {
    runPs(
        scriptCtx,
        'scripts\\ci\\stop_monitor.ps1',
        "-PidFile \"${scriptCtx.env.MONITOR_PID_FILE}\" -StopFlag \"${scriptCtx.env.MONITOR_STOP_FLAG}\" -WaitSeconds 10"
    )
}

def runLoadStage(scriptCtx, scenarioName, threads, ramp, loops, duration, jmxFile, resultFile, reportDir) {
    def label = "${scenarioName}_${threads}"

    startMonitor(scriptCtx, label)

    try {
        runPs(scriptCtx, 'scripts\\ci\\ensure_clean_report_dir.ps1', "-ReportDir \"${reportDir}\"")

        scriptCtx.bat """
        "${scriptCtx.env.JMETER_HOME}\\bin\\jmeter.bat" -n -t ${jmxFile} -Jthreads=${threads} -Jramp=${ramp} -Jloops=${loops} -Jduration=${duration} -Jstartup_delay=0 -l ${resultFile} -e -o ${reportDir}
        """
    } finally {
        stopMonitor(scriptCtx)
    }

    int jmeterBreakerStatus = scriptCtx.bat(
        returnStatus: true,
        script: """
        "${scriptCtx.env.PYTHON_EXE}" scripts\\check_jmeter_breaker.py --jtl ${resultFile} --label ${label} --summary "${scriptCtx.env.BREAKER_SUMMARY}" --max-error-rate ${scriptCtx.env.BREAKER_MAX_ERROR_RATE} --max-p95-ms ${scriptCtx.env.BREAKER_MAX_P95_MS} --min-samples 20
        """
    )

    if (jmeterBreakerStatus == 2) {
        scriptCtx.echo "JMeter breaker triggered for ${label}, higher concurrency of same scenario will be skipped."
        return false
    }
    if (jmeterBreakerStatus != 0) {
        scriptCtx.error("JMeter breaker script failed for ${label}")
    }

    int resourceBreakerStatus = scriptCtx.bat(
        returnStatus: true,
        script: """
        "${scriptCtx.env.PYTHON_EXE}" scripts\\check_resource_breaker.py --resource-file "monitoring\\${label}_resources.csv" --label ${label} --output "${scriptCtx.env.RESOURCE_BREAKER_SUMMARY}" --max-system-cpu ${scriptCtx.env.RESOURCE_MAX_SYSTEM_CPU} --max-process-cpu ${scriptCtx.env.RESOURCE_MAX_PROCESS_CPU} --max-process-mem-mb ${scriptCtx.env.RESOURCE_MAX_PROCESS_MEM_MB} --max-threads ${scriptCtx.env.RESOURCE_MAX_THREADS}
        """
    )

    if (resourceBreakerStatus == 2) {
        scriptCtx.echo "Resource breaker triggered for ${label}, higher concurrency of same scenario will be skipped."
        return false
    }
    if (resourceBreakerStatus != 0) {
        scriptCtx.error("Resource breaker script failed for ${label}")
    }

    return true
}

def runScenarioLadder(scriptCtx, scenarioName, jmxFile, plans) {
    for (plan in plans) {
        boolean keepRunning = runLoadStage(
            scriptCtx,
            scenarioName,
            plan.threads,
            plan.ramp,
            plan.loops,
            plan.duration,
            jmxFile,
            "${scenarioName}-result-${plan.threads}.jtl",
            "${scenarioName}-report-${plan.threads}"
        )

        if (!keepRunning) {
            scriptCtx.echo "${scenarioName} load ladder stopped by breaker at ${plan.threads} threads."
            break
        }
    }
}

pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        PROJECT_DIR                 = 'C:\\Users\\siest\\Desktop\\api'
        PYTHON_EXE                  = 'C:\\Users\\siest\\Desktop\\api\\.venv\\Scripts\\python.exe'
        JMETER_HOME                 = 'D:\\apache-jmeter-5.6.3\\apache-jmeter-5.6.3'
        ALLURE_RESULTS              = 'allure-results'

        ENV_FILE                    = '.env'
        ENV_TEST_FILE               = '.env.test'
        ENV_BACKUP_FILE             = '.env.bak'

        BACKEND_PID_FILE            = 'backend.pid'
        MONITOR_PID_FILE            = 'monitor.pid'
        MONITOR_STOP_FLAG           = 'monitor.stop'

        MONITOR_KEYWORD             = 'uvicorn'
        MONITOR_SUMMARY             = 'monitoring\\monitor_summary.csv'
        BREAKER_SUMMARY             = 'monitoring\\breaker_summary.csv'
        RESOURCE_BREAKER_SUMMARY    = 'monitoring\\resource_breaker_summary.csv'

        BREAKER_MAX_ERROR_RATE      = '1'
        BREAKER_MAX_P95_MS          = '1000'

        RESOURCE_MAX_SYSTEM_CPU     = '95'
        RESOURCE_MAX_PROCESS_CPU    = '160'
        RESOURCE_MAX_PROCESS_MEM_MB = '2048'
        RESOURCE_MAX_THREADS        = '2000'

        PYTHONIOENCODING            = 'utf-8'
    }

    stages {
        stage('Precheck') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    if not exist "%PYTHON_EXE%" exit /b 1
                    if not exist "requirements.txt" exit /b 1
                    if not exist "%ENV_TEST_FILE%" exit /b 1
                    if not exist "app\\main.py" exit /b 1
                    if not exist "tests" exit /b 1
                    if not exist "docker-compose.yml" exit /b 1
                    if not exist "jmeter\\health_baseline.jmx" exit /b 1
                    if not exist "jmeter\\status_load.jmx" exit /b 1
                    if not exist "jmeter\\page_polling_load.jmx" exit /b 1
                    if not exist "scripts\\monitor_resources.py" exit /b 1
                    if not exist "scripts\\check_jmeter_breaker.py" exit /b 1
                    if not exist "scripts\\check_resource_breaker.py" exit /b 1
                    if not exist "scripts\\ci\\cleanup.ps1" exit /b 1
                    if not exist "scripts\\ci\\start_backend.ps1" exit /b 1
                    if not exist "scripts\\ci\\stop_backend.ps1" exit /b 1
                    if not exist "scripts\\ci\\smoke_check.ps1" exit /b 1
                    if not exist "scripts\\ci\\start_monitor.ps1" exit /b 1
                    if not exist "scripts\\ci\\stop_monitor.ps1" exit /b 1
                    if not exist "scripts\\ci\\ensure_clean_report_dir.ps1" exit /b 1
                    if not exist "%JMETER_HOME%\\bin\\jmeter.bat" exit /b 1

                    docker info >nul 2>nul
                    if errorlevel 1 exit /b 1
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
                    '''
                }
            }
        }

        stage('Start Docker Services') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat 'docker compose up -d'
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
                    script {
                        runPs(
                            this,
                            'scripts\\ci\\cleanup.ps1',
                            "-AllureResults \"${env.ALLURE_RESULTS}\" -BackendPidFile \"${env.BACKEND_PID_FILE}\" -MonitorPidFile \"${env.MONITOR_PID_FILE}\" -StopFlag \"${env.MONITOR_STOP_FLAG}\""
                        )
                    }
                }
            }
        }

        stage('Kill Old Backend On Port 8000') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    script {
                        runPs(this, 'scripts\\ci\\stop_backend.ps1', "-Port 8000 -PidFile \"${env.BACKEND_PID_FILE}\"")
                    }
                }
            }
        }

        stage('Start Backend') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    script {
                        runPs(this, 'scripts\\ci\\start_backend.ps1', "-PythonExe \"${env.PYTHON_EXE}\" -PidFile \"${env.BACKEND_PID_FILE}\"")
                    }
                }
            }
        }

        stage('Smoke Check') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    script {
                        runPs(this, 'scripts\\ci\\smoke_check.ps1', "-Url \"http://127.0.0.1:8000/\"")
                    }
                }
            }
        }

        stage('Run Pytest') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '"%PYTHON_EXE%" -m pytest tests --alluredir=%ALLURE_RESULTS%'
                }
            }
        }

        stage('Run JMeter - Health Baseline') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    script {
                        runPs(this, 'scripts\\ci\\ensure_clean_report_dir.ps1', '-ReportDir "health-report"')
                    }
                    bat '"%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\health_baseline.jmx -Jthreads=5 -Jramp=5 -Jloops=10 -Jduration=30 -Jstartup_delay=0 -l health-result.jtl -e -o health-report'
                }
            }
        }

        stage('Run Status Load Ladder') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    script {
                        def plans = [
                            [threads: 20,  ramp: 5,  loops: 40, duration: 60],
                            [threads: 50,  ramp: 10, loops: 40, duration: 60],
                            [threads: 100, ramp: 15, loops: 40, duration: 60],
                            [threads: 200, ramp: 20, loops: 40, duration: 60],
                            [threads: 300, ramp: 30, loops: 40, duration: 60]
                        ]
                        runScenarioLadder(this, "status", "jmeter\\status_load.jmx", plans)
                    }
                }
            }
        }

        stage('Run Polling Load Ladder') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    script {
                        def plans = [
                            [threads: 100,  ramp: 5, loops: 999999, duration: 120],
                            [threads: 300,  ramp: 5, loops: 999999, duration: 120],
                            [threads: 500,  ramp: 5, loops: 999999, duration: 120],
                            [threads: 800,  ramp: 5, loops: 999999, duration: 120],
                            [threads: 1000, ramp: 5, loops: 999999, duration: 120],
                            [threads: 1300, ramp: 5, loops: 999999, duration: 120],
                            [threads: 1500, ramp: 5, loops: 999999, duration: 120]
                        ]
                        runScenarioLadder(this, "polling", "jmeter\\page_polling_load.jmx", plans)
                    }
                }
            }
        }
    }

    post {
        always {
            dir("${env.PROJECT_DIR}") {
                script {
                    stopMonitor(this)
                    runPs(this, 'scripts\\ci\\stop_backend.ps1', "-Port 8000 -PidFile \"${env.BACKEND_PID_FILE}\"")
                }

                archiveArtifacts artifacts: 'allure-results/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'health-report/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'status-report-*/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'polling-report-*/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: '*-result-*.jtl', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'monitoring/**', fingerprint: true, allowEmptyArchive: true

                allure([
                    includeProperties: false,
                    jdk: '',
                    results: [[path: 'allure-results']]
                ])

                bat '''
                if exist "%ENV_FILE%" del /f /q "%ENV_FILE%"
                if exist "%ENV_BACKUP_FILE%" ren "%ENV_BACKUP_FILE%" "%ENV_FILE%"
                '''
            }
        }

        success {
            echo 'Pipeline succeeded.'
        }

        failure {
            echo 'Pipeline failed. Check console output and monitoring artifacts.'
        }
    }
}