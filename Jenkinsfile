def runPs(scriptCtx, file, args = '') {
    def scriptPath = file.replace('/', '\\')
    if (!(scriptPath.length() > 2 && scriptPath[1] == ':' && scriptPath[2] == '\\') && !scriptPath.startsWith('.\\')) {
        scriptPath = ".\\${scriptPath}"
    }
    scriptCtx.bat """
    cd /d "${scriptCtx.env.PROJECT_DIR}"
    if not exist "${scriptPath}" exit /b 1
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& '${scriptPath}' ${args}"
    """
}

def runPsStatus(scriptCtx, file, args = '') {
    def scriptPath = file.replace('/', '\\')
    if (!(scriptPath.length() > 2 && scriptPath[1] == ':' && scriptPath[2] == '\\') && !scriptPath.startsWith('.\\')) {
        scriptPath = ".\\${scriptPath}"
    }
    return scriptCtx.bat(
        returnStatus: true,
        script: """
        cd /d "${scriptCtx.env.PROJECT_DIR}"
        if not exist "${scriptPath}" exit /b 1
        powershell -NoProfile -ExecutionPolicy Bypass -Command "& '${scriptPath}' ${args}"
        """
    )
}

def parseEnvValue(rawValue) {
    def value = rawValue.trim()
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        return value.substring(1, value.length() - 1)
    }
    return value
}

def formatEnvValue(rawValue) {
    def value = rawValue == null ? '' : rawValue.toString()
    if (value.contains(' ') || value.contains('#')) {
        return "\"${value.replace('"', '\\"')}\""
    }
    return value
}

def loadDotEnv(scriptCtx, filePath) {
    def values = [:]
    if (!scriptCtx.fileExists(filePath)) {
        return values
    }

    scriptCtx.readFile(filePath).split(/\r?\n/).each { rawLine ->
        def line = rawLine.trim()
        if (!line || line.startsWith('#') || !line.contains('=')) {
            return
        }
        def parts = line.split('=', 2)
        values[parts[0].trim()] = parseEnvValue(parts[1])
    }
    return values
}

def writeDotEnv(scriptCtx, templatePath, outputPath, overrides) {
    def rendered = scriptCtx.readFile(templatePath).split(/\r?\n/, -1).collect { rawLine ->
        def trimmed = rawLine.trim()
        if (!trimmed || trimmed.startsWith('#') || !rawLine.contains('=')) {
            return rawLine
        }

        def parts = rawLine.split('=', 2)
        def key = parts[0].trim()
        if (!overrides.containsKey(key)) {
            return rawLine
        }

        return "${key}=${formatEnvValue(overrides[key])}"
    }.join('\n')

    scriptCtx.writeFile(file: outputPath, text: "${rendered}\n")
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
        "${scriptCtx.env.JMETER_HOME}\\bin\\jmeter.bat" -n -t ${jmxFile} -Jthreads=${threads} -Jramp=${ramp} -Jloops=${loops} -Jduration=${duration} -Jstartup_delay=0 -Jauth_user=${scriptCtx.env.AUTH_USERNAME} -Jauth_password=${scriptCtx.env.AUTH_PASSWORD} -l ${resultFile} -e -o ${reportDir}
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

    parameters {
        string(name: 'HOST', defaultValue: '127.0.0.1', description: '服务监听地址')
        string(name: 'PORT', defaultValue: '8000', description: '服务监听端口')
        string(name: 'AUTH_USERNAME', defaultValue: 'admin', description: '管理员用户名')
        password(name: 'AUTH_PASSWORD', defaultValue: '', description: '管理员密码')
        password(name: 'ADMIN_REGISTRATION_CODE', defaultValue: '', description: '管理员注册码')
        string(name: 'PYTHON_EXE', defaultValue: '', description: 'Python 解释器绝对路径')
        string(name: 'JMETER_HOME', defaultValue: '', description: 'JMeter 根目录绝对路径')
        string(name: 'MYSQL_HOST', defaultValue: '127.0.0.1', description: 'MySQL 主机')
        string(name: 'MYSQL_PORT', defaultValue: '3307', description: 'MySQL 端口')
        string(name: 'MYSQL_USER', defaultValue: 'root', description: 'MySQL 用户')
        password(name: 'MYSQL_PASSWORD', defaultValue: '', description: 'MySQL 密码')
        string(name: 'MYSQL_DB', defaultValue: 'test_db', description: 'MySQL 数据库名')
        string(name: 'REDIS_HOST', defaultValue: '127.0.0.1', description: 'Redis 主机')
        string(name: 'REDIS_PORT', defaultValue: '6379', description: 'Redis 端口')
        string(name: 'REDIS_DB', defaultValue: '1', description: 'Redis 数据库编号')
        password(name: 'REDIS_PASSWORD', defaultValue: '', description: 'Redis 密码')
    }

    environment {
        ALLURE_RESULTS              = 'allure-results'

        ENV_FILE                    = '.env'
        ENV_TEMPLATE_FILE           = '.env.test.example'
        ENV_BACKUP_FILE             = '.env.bak'

        BACKEND_PID_FILE            = 'backend.pid'
        BACKEND_LOG_FILE            = 'backend.log'
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
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Resolve Env') {
            steps {
                script {
                    env.PROJECT_DIR = pwd()
                }
            }
        }

        stage('Precheck') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    if not exist "requirements.txt" exit /b 1
                    if not exist "requirements-dev.txt" exit /b 1
                    if not exist "%ENV_TEMPLATE_FILE%" exit /b 1
                    if not exist "app\\main.py" exit /b 1
                    if not exist "tests" exit /b 1
                    if not exist "docker-compose.yml" exit /b 1
                    if not exist "jmeter\\health_baseline.jmx" exit /b 1
                    if not exist "jmeter\\status_load.jmx" exit /b 1
                    if not exist "jmeter\\events_load.jmx" exit /b 1
                    if not exist "jmeter\\dashboard_mix_load.jmx" exit /b 1
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
                    if not exist "scripts\\ci\\check_realtime_smoke.py" exit /b 1

                    docker info >nul 2>nul
                    if errorlevel 1 exit /b 1
                    '''
                }
            }
        }

        stage('Prepare Env') {
            steps {
                script {
                    def templatePath = "${env.PROJECT_DIR}\\${env.ENV_TEMPLATE_FILE}"
                    def outputPath = "${env.PROJECT_DIR}\\${env.ENV_FILE}"
                    def templateEnv = loadDotEnv(this, templatePath)

                    if (fileExists(outputPath)) {
                        bat '''
                        if exist "%ENV_BACKUP_FILE%" del /f /q "%ENV_BACKUP_FILE%"
                        copy /Y "%ENV_FILE%" "%ENV_BACKUP_FILE%" >nul
                        '''
                    }

                    def resolvedEnv = [
                        HOST: params.HOST ?: templateEnv.HOST ?: '',
                        PORT: params.PORT ?: templateEnv.PORT ?: '',
                        PYTHON_EXE: params.PYTHON_EXE ?: templateEnv.PYTHON_EXE ?: '',
                        JMETER_HOME: params.JMETER_HOME ?: templateEnv.JMETER_HOME ?: '',
                        AUTH_USERNAME: params.AUTH_USERNAME ?: templateEnv.AUTH_USERNAME ?: '',
                        AUTH_PASSWORD: params.AUTH_PASSWORD ?: templateEnv.AUTH_PASSWORD ?: '',
                        AUTH_PASSWORD_HASH: env.AUTH_PASSWORD_HASH ?: templateEnv.AUTH_PASSWORD_HASH ?: '',
                        ADMIN_REGISTRATION_CODE: params.ADMIN_REGISTRATION_CODE ?: templateEnv.ADMIN_REGISTRATION_CODE ?: '',
                        MYSQL_HOST: params.MYSQL_HOST ?: templateEnv.MYSQL_HOST ?: '',
                        MYSQL_PORT: params.MYSQL_PORT ?: templateEnv.MYSQL_PORT ?: '',
                        MYSQL_USER: params.MYSQL_USER ?: templateEnv.MYSQL_USER ?: '',
                        MYSQL_PASSWORD: params.MYSQL_PASSWORD ?: templateEnv.MYSQL_PASSWORD ?: '',
                        MYSQL_DB: params.MYSQL_DB ?: templateEnv.MYSQL_DB ?: '',
                        REDIS_HOST: params.REDIS_HOST ?: templateEnv.REDIS_HOST ?: '',
                        REDIS_PORT: params.REDIS_PORT ?: templateEnv.REDIS_PORT ?: '',
                        REDIS_DB: params.REDIS_DB ?: templateEnv.REDIS_DB ?: '',
                        REDIS_PASSWORD: params.REDIS_PASSWORD ?: templateEnv.REDIS_PASSWORD ?: '',
                    ]

                    writeDotEnv(this, templatePath, outputPath, resolvedEnv)
                }
            }
        }

        stage('Reload Env') {
            steps {
                script {
                    def envFilePath = "${env.PROJECT_DIR}\\${env.ENV_FILE}"
                    def fileEnv = loadDotEnv(this, envFilePath)

                    env.BASE_URL = "http://${fileEnv.HOST}:${fileEnv.PORT}"
                    env.AUTH_USERNAME = fileEnv.AUTH_USERNAME
                    env.AUTH_PASSWORD = fileEnv.AUTH_PASSWORD
                    env.ADMIN_REGISTRATION_CODE = fileEnv.ADMIN_REGISTRATION_CODE
                    env.PYTHON_EXE = fileEnv.PYTHON_EXE
                    env.JMETER_HOME = fileEnv.JMETER_HOME
                }
            }
        }

        stage('Validate Runtime Config') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    if "%BASE_URL%"=="" exit /b 1
                    if "%AUTH_USERNAME%"=="" exit /b 1
                    if "%AUTH_USERNAME%"=="__CHANGE_ME__" exit /b 1
                    if "%AUTH_PASSWORD%"=="" exit /b 1
                    if "%AUTH_PASSWORD%"=="__CHANGE_ME__" exit /b 1
                    if "%ADMIN_REGISTRATION_CODE%"=="" exit /b 1
                    if "%ADMIN_REGISTRATION_CODE%"=="__CHANGE_ME__" exit /b 1
                    if "%PYTHON_EXE%"=="" exit /b 1
                    if "%JMETER_HOME%"=="" exit /b 1
                    if not exist "%PYTHON_EXE%" exit /b 1
                    if not exist "%JMETER_HOME%\\bin\\jmeter.bat" exit /b 1
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
                    "%PYTHON_EXE%" -m pip install -r requirements-dev.txt
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
                        runPs(this, 'scripts\\ci\\start_backend.ps1', "-PythonExe \"${env.PYTHON_EXE}\" -PidFile \"${env.BACKEND_PID_FILE}\" -LogFile \"${env.BACKEND_LOG_FILE}\" -StartupWaitSeconds 5")
                    }
                }
            }
        }

        stage('Smoke Check') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    script {
                        runPs(this, 'scripts\\ci\\smoke_check.ps1', "-Url \"${env.BASE_URL}/\"")
                    }
                }
            }
        }

        stage('Realtime Smoke Check') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    bat '''
                    "%PYTHON_EXE%" scripts\\ci\\check_realtime_smoke.py --base-url "%BASE_URL%" --username "%AUTH_USERNAME%" --password "%AUTH_PASSWORD%"
                    '''
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

        stage('Run Events Load Ladder') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    script {
                        def plans = [
                            [threads: 20,  ramp: 5,  loops: 40, duration: 60],
                            [threads: 50,  ramp: 10, loops: 40, duration: 60],
                            [threads: 100, ramp: 15, loops: 40, duration: 60],
                            [threads: 200, ramp: 20, loops: 40, duration: 60]
                        ]
                        runScenarioLadder(this, "events", "jmeter\\events_load.jmx", plans)
                    }
                }
            }
        }

        stage('Run Dashboard Mixed Load Ladder') {
            steps {
                dir("${env.PROJECT_DIR}") {
                    script {
                        def plans = [
                            [threads: 100, ramp: 5, loops: 999999, duration: 120],
                            [threads: 300, ramp: 5, loops: 999999, duration: 120],
                            [threads: 500, ramp: 5, loops: 999999, duration: 120],
                            [threads: 800, ramp: 5, loops: 999999, duration: 120]
                        ]
                        runScenarioLadder(this, "dashboard", "jmeter\\dashboard_mix_load.jmx", plans)
                    }
                }
            }
        }
    }

    post {
        always {
            dir("${env.PROJECT_DIR}") {
                script {
                    int stopMonitorStatus = runPsStatus(this, 'scripts\\ci\\stop_monitor.ps1', "-PidFile \"${env.MONITOR_PID_FILE}\" -StopFlag \"${env.MONITOR_STOP_FLAG}\" -WaitSeconds 10")
                    if (stopMonitorStatus != 0) {
                        echo "Cleanup warning: stop_monitor.ps1 exited with code ${stopMonitorStatus}"
                    }

                    int stopBackendStatus = runPsStatus(this, 'scripts\\ci\\stop_backend.ps1', "-Port 8000 -PidFile \"${env.BACKEND_PID_FILE}\"")
                    if (stopBackendStatus != 0) {
                        echo "Cleanup warning: stop_backend.ps1 exited with code ${stopBackendStatus}"
                    }
                }

                archiveArtifacts artifacts: 'allure-results/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'backend.log', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'health-report/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'status-report-*/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'events-report-*/**', fingerprint: true, allowEmptyArchive: true
                archiveArtifacts artifacts: 'dashboard-report-*/**', fingerprint: true, allowEmptyArchive: true
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
