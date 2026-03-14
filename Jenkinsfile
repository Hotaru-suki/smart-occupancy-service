pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    environment {
        PYTHONIOENCODING = 'utf-8'
        JMETER_HOME = 'D:\\apache-jmeter-5.6.3'
        ALLURE_RESULTS = 'allure-results'
        BACKEND_LOG = 'backend.log'
        BACKEND_PID_FILE = 'backend.pid'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Prepare Test Env') {
            steps {
                bat '''
                if exist .env del /f /q .env
                copy /Y .env.test .env
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '''
                python -m pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Clean Old Results') {
            steps {
                bat """
                if exist %ALLURE_RESULTS% rmdir /s /q %ALLURE_RESULTS%
                if exist allure-report rmdir /s /q allure-report
                if exist health-report rmdir /s /q health-report
                if exist status-report rmdir /s /q status-report
                if exist polling-report rmdir /s /q polling-report

                if exist health-result.jtl del /f /q health-result.jtl
                if exist status-result.jtl del /f /q status-result.jtl
                if exist polling-result.jtl del /f /q polling-result.jtl

                if exist %BACKEND_LOG% del /f /q %BACKEND_LOG%
                if exist %BACKEND_PID_FILE% del /f /q %BACKEND_PID_FILE%
                """
            }
        }

        stage('Start Backend') {
            steps {
                bat '''
                powershell -Command ^
                  "$p = Start-Process python -ArgumentList '-m','uvicorn','app.main:app','--host','127.0.0.1','--port','8000' -RedirectStandardOutput 'backend.log' -RedirectStandardError 'backend.log' -PassThru; ^
                   $p.Id | Out-File -FilePath 'backend.pid' -Encoding ascii"
                '''
                bat 'timeout /t 8 >nul'
            }
        }

        stage('Smoke Check') {
            steps {
                bat '''
                python -c "import requests; r=requests.get('http://127.0.0.1:8000/', timeout=10); print(r.status_code); assert r.status_code == 200"
                '''
            }
        }

        stage('Run Pytest') {
            steps {
                bat '''
                pytest tests --alluredir=%ALLURE_RESULTS%
                '''
            }
        }

        stage('Run JMeter - Health Baseline') {
            steps {
                bat '''
                "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\health_baseline.jmx -l health-result.jtl -e -o health-report
                '''
            }
        }

        stage('Run JMeter - Status Load') {
            steps {
                bat '''
                "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\status_load.jmx -l status-result.jtl -e -o status-report
                '''
            }
        }

        stage('Run JMeter - Page Polling Load') {
            steps {
                bat '''
                "%JMETER_HOME%\\bin\\jmeter.bat" -n -t jmeter\\page_polling_load.jmx -l polling-result.jtl -e -o polling-report
                '''
            }
        }
    }

    post {
        always {
            script {
                if (fileExists(env.BACKEND_PID_FILE)) {
                    bat '''
                    for /f %%i in (backend.pid) do taskkill /PID %%i /T /F
                    '''
                }
            }

            archiveArtifacts artifacts: 'backend.log', fingerprint: true, allowEmptyArchive: true
            archiveArtifacts artifacts: 'allure-results/**', fingerprint: true, allowEmptyArchive: true
            archiveArtifacts artifacts: '*.jtl', fingerprint: true, allowEmptyArchive: true
            archiveArtifacts artifacts: '*-report/**', fingerprint: true, allowEmptyArchive: true
        }

        success {
            echo 'Pipeline succeeded: backend, pytest, and JMeter all completed successfully.'
        }

        failure {
            echo 'Pipeline failed. Please check backend.log, pytest output, and JMeter reports.'
        }

        cleanup {
            bat '''
            if exist .env del /f /q .env
            if exist backend.pid del /f /q backend.pid
            '''
        }
    }
}