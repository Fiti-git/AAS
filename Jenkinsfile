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

        stage('Stop Existing Containers') {
            steps {
                script {
                    // Stop and remove any existing containers
                    echo "Stopping and removing any existing containers..."
                    sh "$DOCKER_COMPOSE_CMD down"
                    // Ensure any lingering containers are also stopped and removed
                    sh 'docker ps -q --filter name=aas_db | xargs -r docker stop'
                    sh 'docker ps -q --filter name=pgadmin | xargs -r docker stop'
                    sh 'docker ps -q --filter name=web | xargs -r docker stop'
                    sh 'docker ps -q --filter name=aas_db | xargs -r docker rm'
                    sh 'docker ps -q --filter name=pgadmin | xargs -r docker rm'
                    sh 'docker ps -q --filter name=web | xargs -r docker rm'
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
                    // Wait for a few seconds to allow any processes to stabilize before starting the containers
                    echo "Waiting for containers to stabilize..."
                    sh 'sleep 10' // Adjust time if needed

                    // Start the containers
                    echo "Starting containers..."
                    sh "$DOCKER_COMPOSE_CMD up -d"
                }
            }
        }

        stage('Run Migrations') {
            steps {
                script {
                    // Wait for the web container to be up and running
                    echo "Waiting for web container to be ready..."
                    sh "docker-compose -f docker-compose.yml exec -T web wait-for-it.sh db:5432 --timeout=60 --strict -- echo 'db is up and running'"

                    echo "Running Django migrations..."
                    sh "$DOCKER_COMPOSE_CMD exec -T web python manage.py migrate --noinput"
                }
            }
        }


        stage('Check Containers') {
            steps {
                script {
                    // Verify that the containers are running
                    echo "Checking running containers..."
                    sh 'docker ps'
                }
            }
        }
    }

    post {
        always {
            echo "Cleaning up workspace..."
            cleanWs() // Clean up workspace after the build
        }

        success {
            echo "Pipeline executed successfully!"
        }

        failure {
            echo "Pipeline failed!"
        }
    }
}
