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
                sh 'python -m venv .venv'
                sh './.venv/Scripts/pip install --upgrade pip'
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    if (fileExists('requirements.txt')) {
                        sh './.venv/Scripts/pip install -r requirements.txt'
                    } else {
                        echo 'No requirements.txt found — skipping dependency install.'
                    }
                }
            }
        }

        stage('Run Django Checks') {
            steps {
                sh './.venv/Scripts/python manage.py check'
            }
        }

        stage('Run Migrations') {
            steps {
                sh './.venv/Scripts/python manage.py migrate'
            }
        }

        stage('Run Tests') {
            steps {
                sh './.venv/Scripts/python manage.py test'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
