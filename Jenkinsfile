pipeline {
  agent any
  stages {
    stage('Prepare Build') {
      steps {
        script {
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
          sh "sed -i 's/local/awsdev/g' front-end/Dockerfile"
          def frontendImage = docker.build("fecnxg-frontend:${VERSION}", 'front-end/')

          docker.withRegistry('https://813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-frontend') {
            frontendImage.push()
          }

          sh "sed -i 's/awsdev/awsuat/g' front-end/Dockerfile"
          def frontendImageUAT = docker.build("fecnxg-frontend:${VERSION}uat", 'front-end/')

          docker.withRegistry('https://813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-frontend') {
            frontendImageUAT.push()
          }

          sh "sed -i 's/awsuat/awsqa/g' front-end/Dockerfile"
          def frontendImageQA = docker.build("fecnxg-frontend:${VERSION}qa", 'front-end/')

          docker.withRegistry('https://813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-frontend') {
            frontendImageQA.push()
          }
        }
      }

    }

    stage('Build Flywaydb') {
      when { branch "develop" }
        steps { 
            script {
              sh("sed -i '11d' data/flyway_migration.sh")
              def flywayImage = docker.build("fecfile-flyway-db:${VERSION}", 'data/')
              
              docker.withRegistry('https://813218302951.dkr.ecr.us-east-1.amazonaws.com/fecfile-flyway-db') {
                  flywayImage.push()
              }
              sh("bash data/deploy.sh ${VERSION} fecfile-frontend-dev-db.casvptvnuxni.us-east-1.rds.amazonaws.com dev ")
            }
        }    
    }
    stage ('Deployments'){
      when { branch "develop" }
      parallel {
        stage('Deploy backend-api to DEV environment'){
          steps {
            sh "kubectl --context=arn:aws:eks:us-east-1:813218302951:cluster/fecfile --namespace=dev set image deployment/fecfile-backend-api fecfile-backend-api=813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-django-backend:${VERSION}"
          }
        }
        stage('Deploy front-end to DEV environment'){
          steps{
            sh "kubectl --context=arn:aws:eks:us-east-1:813218302951:cluster/fecfile --namespace=dev set image deployment/fecfile-frontend fecfile-frontend=813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-frontend:${VERSION}"
          }
        }
      }
    }
    stage('Code Quality') {
      steps {
        code_quality()
      }
    }
  }
  post {
    success {

      message_on_dev("good", ": Deployed ${VERSION} to k8s https://dev-fecfile.efdev.fec.gov/") 
    }
    failure {
      message_on_dev("danger", ": Deployement of ${VERSION} failed!")
    }
  }
}

def message_on_dev(String col, String mess){
  if( env.BRANCH_NAME == 'develop'){
    slackSend color: col, message: env.BRANCH_NAME + mess
  }
}

def code_quality() {
    //Build python3.6 virtualenv
    sh """
      virtualenv -p python36 .venv
      source .venv/bin/activate
      pip3 install flake8 flake8-junit-report
			mkdir -p reports
      flake8 --exit-zero django-backend --output-file reports/${BUILD_ID}-${VERSION}-flake8.txt
      flake8_junit reports/${BUILD_ID}-${VERSION}-flake8.txt reports/${BUILD_ID}-${VERSION}-flake8_junit.xml
      deactivate
      rm -fr .venv
    """
    junit '**/reports/*.xml'
}
