pipeline {
    agent any

    stages {
        stage('Build Django Image') {
            steps {
                dir('AAS') {
                    sh '''
                    docker-compose -p aas-backend-pipeline down --remove-orphans || true
                    docker-compose -p aas-backend-pipeline build web
                    '''
                }
            }
        }

        stage('Start Containers') {
            steps {
                dir('AAS') {
                    sh 'docker-compose -p aas-backend-pipeline up -d db web'
                }
            }
        }

        stage('Wait for DB') {
            steps {
                dir('AAS') {
                    script {
                        timeout(time: 2, unit: 'MINUTES') {
                            waitUntil {
                                def result = sh(script: "docker-compose -p aas-backend-pipeline exec db pg_isready -U postgres", returnStatus: true)
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
        }

        stage('Run Migrations') {
            steps {
                dir('AAS') {
                    retry(3) {
                        sh "docker-compose -p aas-backend-pipeline run --rm web python manage.py migrate"
                    }
                }
            }
        }
    }
}
