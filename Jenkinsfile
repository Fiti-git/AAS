pipeline {
    agent any

    environment {
        DJANGO_IMAGE = 'django_backend'
        DJANGO_COMPOSE_FILE = 'docker-compose.yml'
    }

    stages {
        stage('Checkout') {
            steps {
                git 'https://github.com/Fiti-git/AAS.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Build Docker image for Django
                    sh 'docker-compose -f $DJANGO_COMPOSE_FILE build'
                }
            }
        }

        stage('Run Docker Container') {
            steps {
                script {
                    // Run the container for Django
                    sh 'docker-compose -f $DJANGO_COMPOSE_FILE up -d'
                }
            }
        }

        stage('Run Migrations') {
            steps {
                script {
                    // Run Django migrations
                    sh 'docker-compose exec web python manage.py migrate'
                }
            }
        }

        stage('Check Containers') {
            steps {
                script {
                    // Verify that the container is running
                    sh 'docker ps'
                }
            }
        }
    }

    post {
        always {
            cleanWs() // Clean up workspace after build
        }
    }
}
