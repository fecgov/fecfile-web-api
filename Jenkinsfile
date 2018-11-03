pipeline {

  agent any

  stages {

    stage('Prepare Build') {
      steps {
                script
                {
                    hash = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
                    VERSION = hash.take(7)
                    currentBuild.displayName = "#${BUILD_ID}-${VERSION}"

                    sh("eval \$(aws ecr --region us-east-1 get-login --no-include-email)")
                }
            }
    }

    stage('Build backend') {
      steps {
        script {

          def backendImage = docker.build("fecnxg-django-backend:${VERSION}", 'django-backend/')

          docker.withRegistry('https://813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-django-backend') {
            backendImage.push()
          }
        }
      }
    }

    stage('Build frontend') {
      steps {
        script {
          def frontendImage = docker.build("fecnxg-frontend:${VERSION}", 'front-end/')

          docker.withRegistry('https://813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-frontend') {
            frontendImage.push()
          }

          def frontendNginxImage = docker.build("fecnxg-frontend-nginx:${VERSION}", 'front-end/ -f front-end/Dockerfile-nginx')

          docker.withRegistry('https://813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-frontend-nginx') {
            frontendNginxImage.push()
          }
        }
      }

    }
  }
}
