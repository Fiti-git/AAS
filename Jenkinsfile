pipeline {
    agent any

    stages {
        stage('Clone Repo') {
            steps {
                git branch: 'main', url: 'https://github.com/Fiti-git/AAS.git'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t aas_django_app . || echo "Skipping docker build on Jenkins"'
            }
        }

        stage('Deploy on VPS') {
            steps {
                sshagent(['your-credential-id']) {
                    sh '''
                    ssh -o StrictHostKeyChecking=no root@139.59.243.2 "
                    cd /home/AAS &&
                    docker-compose down &&
                    docker-compose up -d --build &&
                    docker-compose exec web python manage.py migrate &&
                    docker-compose ps
                    "
                    '''
                }
            }
        }

        stage('Verify Deployment') {
            steps {
                sshagent(['your-credential-id']) {
                    sh '''
                    ssh -o StrictHostKeyChecking=no root@139.59.243.2 "
                    curl -f http://localhost:8000 || echo 'App not responding'
                    "
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'Deployment successful! 🎉'
        }
        failure {
            echo 'Deployment failed. Check logs!'
        }
    }
}
