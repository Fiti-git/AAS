pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm  // pulls latest code from repo
            }
        }

        stage('Stop Django Container') {
            steps {
                sh 'docker-compose stop django'  // only stop django container, keep db running
            }
        }

        stage('Build Django Image') {
            steps {
                sh 'docker-compose build django'  // build new django image with latest code
            }
        }

        stage('Start Django Container') {
            steps {
                sh 'docker-compose up -d --no-deps django'  // start django container only, don't restart db or pgadmin
            }
        }

        stage('Wait for DB') {
            steps {
                script {
                    timeout(time: 2, unit: 'MINUTES') {
                        waitUntil {
                            def result = sh(
                                script: "docker-compose exec db pg_isready -U postgres",
                                returnStatus: true
                            )
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
                    sh 'docker-compose exec django python manage.py migrate'
                }
            }
        }
    }
}
