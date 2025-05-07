pipeline {
    agent any

    environment {
        VENV_DIR = ".venv"
    }

    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/Fiti-git/AAS.git'
            }
        }

        stage('Set Up Python Environment') {
            steps {
                sh 'python3 -m venv .venv'
                sh './.venv/bin/pip install --upgrade pip'
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    if (fileExists('requirements.txt')) {
                        sh './.venv/bin/pip install -r requirements.txt'
                    } else {
                        echo 'No requirements.txt found — skipping dependency install.'
                    }
                }
            }
        }

        stage('Run Django Checks') {
            steps {
                sh './.venv/bin/python manage.py check'
            }
        }

        stage('Run Migrations') {
            steps {
                sh './.venv/bin/python manage.py migrate'
            }
        }

        stage('Run Tests') {
            steps {
                sh './.venv/bin/python manage.py test'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
