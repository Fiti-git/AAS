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
                echo "Skipping docker build on Jenkins, build will run on VPS."
                // if your jenkins server has docker, you can uncomment this line to build locally
                // sh 'docker build -t aas_django_app . || echo "Skipping docker build on Jenkins"'
            }
        }

        stage('Deploy on VPS') {
            steps {
                sshagent(['3d42b9b2-6283-468e-9eca-7bcb797b8b2f']) {
                    sh '''
                    ssh -o StrictHostKeyChecking=no root@139.59.243.2 "
                    cd /home/AAS &&
                    git pull origin main &&
                    docker-compose down &&
                    docker-compose up -d --build &&
                    sleep 10 &&
                    docker-compose exec web python manage.py makemigrations --noinput &&
                    docker-compose exec web python manage.py migrate --noinput &&
                    docker-compose ps
                    "
                    '''
                }
            }
        }

        stage('Verify Deployment') {
            steps {
                sshagent(['3d42b9b2-6283-468e-9eca-7bcb797b8b2f']) {
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
