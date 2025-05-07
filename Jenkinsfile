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

        stage('Deploy with Gunicorn') {
            steps {
                // Running the Gunicorn server on port 8000 (you can change the port if needed)
                sh './${VENV_DIR}/bin/gunicorn --bind 0.0.0.0:8000 projectname.wsgi:application'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
