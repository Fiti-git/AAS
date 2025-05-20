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
                    script {
                        def webRunning = sh(script: "docker inspect -f '{{.State.Running}}' aas-backend", returnStdout: true).trim()
                        if (webRunning == 'true') {
                            sh 'docker-compose exec web python manage.py migrate'
                        } else {
                            echo "Web container is NOT running! Dumping logs..."
                            sh 'docker logs aas-backend || echo "No logs available"'
                            error "Cannot run migrations because web container is not running"
                        }
                    }
                }
            }
        }
    }
}
