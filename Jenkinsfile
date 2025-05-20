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
                sh 'docker-compose stop web'  // only stop web (Django) container, keep db running
            }
        }

        stage('Build Django Image') {
            steps {
                sh 'docker-compose build web'  // build new web image with latest code
            }
        }

        stage('Start Django Container') {
            steps {
                sh 'docker-compose up -d --no-deps web'  // start web container only, don't restart db
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
                    sh 'docker-compose exec web python manage.py migrate'
                }
            }
        }
    }
}
