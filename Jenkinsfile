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
                }
            }
    }

    stage('Build backend') {
      steps {
        script {
          sh("eval \$(aws ecr get-login --no-include-email)")
          def backendImage = docker.build("fecnxg-django-backend:${VERSION}", 'django-backend/')

          docker.withRegistry('https://813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-django-backend') {
            backendImage.push()
          }

          def frontendImage = docker.build("fecnxg-frontend:${VERSION}", 'frontend/')

          docker.withRegistry('https://813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-frontend') {
            frontendImage.push()
          }
        }
      }

    }
  }
}
