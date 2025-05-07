pipeline {
    agent any

    environment {
        VENV_DIR = ".venv"
    }

    stages {
        stage('Checkout') {
            steps {
                // Explicitly use the 'main' branch to avoid errors
                git branch: 'main', url: 'https://github.com/Fiti-git/AAS.git'
            }
        }

        stage('Set Up Python Environment') {
            steps {
                sh 'python3 -m venv ${VENV_DIR}'
                sh './${VENV_DIR}/bin/pip install --upgrade pip'
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    if (fileExists('requirements.txt')) {
                        sh './${VENV_DIR}/bin/pip install -r requirements.txt'
                    } else {
                        echo 'No requirements.txt found — skipping dependency install.'
                    }
                }
            }
        }

        stage('Run Django Checks') {
            steps {
                sh './${VENV_DIR}/bin/python manage.py check'
            }
        }

        stage('Run Migrations') {
            steps {
                sh './${VENV_DIR}/bin/python manage.py migrate'
            }
        }

        stage('Run Tests') {
            steps {
                sh './${VENV_DIR}/bin/python manage.py test'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
