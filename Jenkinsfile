pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Stop Containers') {
            steps {
                sh 'docker-compose stop'
            }
        }

        stage('Build Images') {
            steps {
                sh 'docker-compose build'
            }
        }

        stage('Start Containers') {
            steps {
                sh 'docker-compose up -d'
            }
        }

        stage('Run Migrations') {
            steps {
                // run django migrations inside the django container
                sh 'docker-compose exec django python manage.py migrate'
            }
        }
    }
}
