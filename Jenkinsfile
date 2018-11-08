pipeline {

  agent any

  stages {

    stage('Prepare Build') {
      steps {
                script
                {
                    // calculate GIT lastest commit short-hash
                    gitCommitHash = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
                    shortCommitHash = gitCommitHash.take(7)
                    // calculate a sample version tag
                    VERSION = shortCommitHash
                    // set the build display name
                    currentBuild.displayName = "#${BUILD_ID}-${VERSION}"
                }
            }
    }

    stage('Build backend') {
      steps {
        script {
          sh("eval \$(aws ecr get-login --no-include-email)")
          def img = docker.build('fecnxg-django-backend:${VERSION}', 'django-backend/')

          docker.withRegistry('813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-django-backend') {
            docker.image('fecnxg-django-backend').push(${VERSION})
          }
        }
      }

    }
  }
}
