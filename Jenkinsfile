pipeline {
    agent any

    environment {
        DJANGO_IMAGE = 'django_backend'
        DJANGO_COMPOSE_FILE = 'docker-compose.yml'
        DOCKER_COMPOSE_CMD = 'docker-compose -f $DJANGO_COMPOSE_FILE'
    }

    stages {
        stage('Checkout') {
            steps {
                // Checkout from the 'main' branch explicitly
                git branch: 'main', url: 'https://github.com/Fiti-git/AAS.git'
            }
        }

        stage('Stop Containers') {
            steps {
                script {
                    // Stop and remove any running containers before starting fresh
                    echo "Stopping and removing any existing containers..."
                    sh "$DOCKER_COMPOSE_CMD down"
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Build Docker image for Django
                    echo "Building Docker image for Django..."
                    sh "$DOCKER_COMPOSE_CMD build"
                }
            }
        }

        stage('Run Docker Container') {
            steps {
                script {
                    // Run the container for Django
                    echo "Starting Django container..."
                    sh "$DOCKER_COMPOSE_CMD up -d"
                }
            }
        }

        stage('Run Migrations') {
            steps {
                script {
                    // Run Django migrations
                    echo "Running Django migrations..."
                    sh "$DOCKER_COMPOSE_CMD exec -T web python manage.py migrate --noinput"
                }
            }
        }

        stage('Check Containers') {
            steps {
                script {
                    // Verify that the container is running
                    echo "Checking running containers..."
                    sh 'docker ps'
                }
            }
        }
    }

    post {
        always {
            echo "Cleaning up workspace..."
            cleanWs() // Clean up workspace after build
        }

        success {
            echo "Pipeline executed successfully!"
        }

        failure {
            echo "Pipeline failed!"
        }
    }
}
