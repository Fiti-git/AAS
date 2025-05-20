pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Stop Django Container') {
            steps {
                sh '''
                docker-compose stop web || true
                docker-compose rm -f web || true
                '''
            }
        }

        stage('Build Django Image') {
            steps {
                sh '''
                docker-compose down --remove-orphans || true
                docker-compose build web
                '''
            }
        }

        stage('Start Containers') {
            steps {
                sh 'docker-compose up -d db web'
            }
        }

        stage('Wait for DB') {
            steps {
                script {
                    timeout(time: 2, unit: 'MINUTES') {
                        waitUntil {
                            def result = sh(script: "docker-compose exec db pg_isready -U postgres", returnStatus: true)
                            if (result == 0) {
                                echo "Postgres is up!"
                                return true
                            } else {
                                echo "Postgres is unavailable - sleeping 2s"
                                sleep 2
                                return false
                            }
                        }
                    }
                }
            }
        }

        stage('Run Migrations') {
            steps {
                retry(3) {
                    sh 'docker-compose exec web python manage.py migrate'
                }
            }
        }
    }
}
