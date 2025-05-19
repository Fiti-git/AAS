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

        stage('Wait for DB') {
            steps {
                sh '''
                    echo "Waiting for Postgres to be ready..."
                    until docker-compose exec db pg_isready -U postgres; do
                        echo "Postgres is unavailable - sleeping 2s"
                        sleep 2
                    done
                    echo "Postgres is up!"
                '''
            }
        }

        stage('Run Migrations') {
            steps {
                sh 'docker-compose exec django python manage.py migrate'
            }
        }
    }
}
