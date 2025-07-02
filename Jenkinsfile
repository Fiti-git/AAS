pipeline {
    agent any

    environment {
        // Define environment variables
        DEPLOY_SERVER = 'root@159.65.254.186'  // The IP address of your server
        DEPLOY_PATH = '/root/AAS'               // Path to deploy on the server
        GIT_REPO = 'https://github.com/Fiti-git/AAS.git' // Your GitHub repository
        SSH_KEY_ID = 'vps-ssh-key'             // Jenkins credential ID for SSH key
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    // Checkout the latest code from GitHub
                    git branch: 'main', url: "${GIT_REPO}"
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Build the Docker image using the Dockerfile
                    sh '''
                    docker build -t aas_web .
                    '''
                }
            }
        }

        stage('Deploy to VPS') {
            steps {
                script {
                    // Use SSH to deploy the app with the credentials from Jenkins
                    sshagent(credentials: [SSH_KEY_ID]) {
                        sh """
                        ssh -o StrictHostKeyChecking=no ${DEPLOY_SERVER} "
                            cd ${DEPLOY_PATH} && 
                            docker-compose down && 
                            docker-compose up -d --build"
                        """
                    }
                }
            }
        }

        stage('Verify Deployment') {
            steps {
                script {
                    // Verify the deployment on the VPS
                    sshagent(credentials: [SSH_KEY_ID]) {
                        sh """
                        ssh ${DEPLOY_SERVER} 'docker ps'
                        """
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Deployment successful!'
        }
        failure {
            echo 'Deployment failed. Check logs for details.'
        }
    }
}
