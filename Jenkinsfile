pipeline {
  agent any
  stages {
    stage('Prepare Build'){
      steps {
        script{
          hash = sh(returnStdout: true, script: 'git rev-parse HEAD').trim()
          VERSION = hash.take(7)
          currentBuild.displayName = "#${BUILD_ID}-${VERSION}"
          sh("eval \$(aws ecr --region us-east-1 get-login --no-include-email)")
        }
      }
    }
    // Deploy to develop branch
    stage('Development') {
      when { branch 'develop'}
      stages {
        stage("Build Images") {
          parallel {
            stage("Backend") {
              steps { buildBack("${VERSION}") }
            }
            stage("front-end") {
              steps { imageBuild("${VERSION}", "awsdev") }
            } 
            stage("Flyway") {
              steps { build_flyway("${VERSION}") }
            }
            //stage("Functions") {
            //  steps { build_functions("${VERSION}")}
            //}
          }
        }
       
        stage("Deploy App") {
          steps {
            //Deploy flyway
            sh("bash data/deploy.sh ${VERSION} fecfile-frontend-dev-db.casvptvnuxni.us-east-1.rds.amazonaws.com dev ")
            //Deploy functions
            //sh("bash scripts/lambda/deploy.sh ${VERSION} fecfile-frontend-dev-db.casvptvnuxni.us-east-1.rds.amazonaws.com dev")
            //deployToK8s(String version, String environment, String deployment, String repo)
            //Deploy backend
            deployToK8s("${VERSION}", "dev","fecfile-backend-api","fecnxg-django-backend")
            //Deploy frontend
            deployToK8s16("${VERSION}", "dev", "fecfile-frontend","fecnxg-frontend")
          }
        }
        stage('Code Quality') {
          steps {
            code_quality()
          }
        }
      }
    }
    //End of developent stage 
    stage('QA'){
      when { branch 'release'}
      stages {
        stage("Build Images"){
          parallel {
            stage("Backend") {
              steps { buildBack("${VERSION}") }
            }
            stage("front-end") {
              steps { imageBuild("${VERSION}qa", "awsqa") }
            } 
            stage("Flyway") {
              steps { build_flyway("${VERSION}") }
            }
            //stage("Functions") {
            //  steps { build_functions("${VERSION}")}
            // }
          }
        }
       
        stage("Deploy App"){
          steps{
            //Deploy flyway
            sh("bash data/deploy.sh ${VERSION} fecfile-frontend-qa-db.casvptvnuxni.us-east-1.rds.amazonaws.com qa ")
            //Deploy functions
            //sh("bash scripts/lambda/deploy.sh ${VERSION} fecfile-frontend-qa-db.casvptvnuxni.us-east-1.rds.amazonaws.com qa ")
            //Deploy backend
            deployToK8s("${VERSION}", "qa","fecfile-backend-api","fecnxg-django-backend")
            //Deploy frontend
            deployToK8s("${VERSION}qa", "qa", "fecfile-frontend","fecnxg-frontend")
          }
        }
      }
    }
    //End of qa stage 
    stage('UAT'){
      when { branch 'master'}
      stages {
        stage("Build Images"){
          parallel {
            stage("Backend") {
              steps { buildBack("${VERSION}") }
            }
            stage("front-end") {
              steps { imageBuild("${VERSION}uat", "awsuat") }
            } 
            stage("Flyway") {
              steps { build_flyway("${VERSION}") }
            }
            //stage("Functions") {
            //  steps { build_functions("${VERSION}")}
            // }
          }
        }
       
        stage("Deploy App"){
          steps{
            //Deploy flyway
            sh("bash data/deploy.sh ${VERSION} fecfile-frontend-uat-db.casvptvnuxni.us-east-1.rds.amazonaws.com uat")
            //Deploy functions
            // sh("bash scripts/lambda/deploy.sh ${VERSION} fecfile-frontend-uat-db.casvptvnuxni.us-east-1.rds.amazonaws.com uat")
            //Deploy backend
            deployToK8s("${VERSION}", "uat","fecfile-backend-api","fecnxg-django-backend")
            //Deploy frontend
            deployToK8s("${VERSION}uat", "uat", "fecfile-frontend","fecnxg-frontend")
          }
        }
      }
    }
    //end of UAT stage
  }

  post {
    always {
      sh " docker image prune -a -f "
    }
    success {
      message_on_dev("good", ": Deployed ${VERSION} to https://fecfile.efdev.fec.gov/") 
    }
    failure {
      message_on_dev("danger", ": Deployement of ${VERSION} to https://fecfile.efdev.fec.gov/ failed!")
    }
  }

}
def message_on_dev(String col, String mess){
  if( env.BRANCH_NAME == 'develop' || env.BRANCH_NAME == 'release' || env.BRANCH_NAME == 'master'){
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
        
def imageBuild(String version, String frontend_env) {
  if(frontend_env == "awsdev"){
    sh("sed -i 's/=local/=${frontend_env}/g' front-end/Dockerfile")
    sh("sed -i 's/VERDEPLOYED/${version}/g' front-end/Dockerfile")
  }
  if (frontend_env == "awsqa") {
    sh("sed -i 's/=local/=${frontend_env}/g' front-end/Dockerfile")
    sh("sed -i 's/awsdev/${frontend_env}/g' front-end/Dockerfile")
    sh("sed -i 's/VERDEPLOYED/${version}/g' front-end/Dockerfile")

  }
  if (frontend_env == "awsuat") {
    sh("sed -i 's/=local/=${frontend_env}/g'  front-end/Dockerfile")
    sh("sed -i 's/awsdev/${frontend_env}/g' front-end/Dockerfile")
    sh("sed -i 's/awsqa/${frontend_env}/g'  front-end/Dockerfile")
    sh("sed -i 's/VERDEPLOYED/${version}/g' front-end/Dockerfile")
    sh("sed -i 's/--source-map=true//g'     front-end/Dockerfile")

  }
 
  def imageB = docker.build("fecnxg-frontend:${version}", 'front-end/')
  docker.withRegistry("https://813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-frontend") {
    imageB.push()
  }
}
def buildBack(String version) {
    def imageBack = docker.build("fecnxg-django-backend:${version}", 'django-backend/')
    docker.withRegistry('https://813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-django-backend') {
        imageBack.push()
    }
}
def build_flyway(String version) {
  sh("sed -i '11d' data/flyway_migration.sh")
  def imageC = docker.build("fecfile-flyway-db:${version}", "data/")
  docker.withRegistry("https://813218302951.dkr.ecr.us-east-1.amazonaws.com/fecfile-flyway-db") {
      imageC.push()
  }
}
def build_functions(String version) {
  
  def imageF = docker.build("fecnxg-functions:${version}", "scripts/lambda/")
  docker.withRegistry("https://813218302951.dkr.ecr.us-east-1.amazonaws.com/fecnxg-functions") {
      imageF.push()
  }
}
def deployToK8s(String version, String environment, String deployment, String repo) {
  sh """ 
    kubectl \
      --context=arn:aws:eks:us-east-1:813218302951:cluster/fecfile4 \
      --namespace=${environment} \
      set image deployment/${deployment} ${deployment}=813218302951.dkr.ecr.us-east-1.amazonaws.com/${repo}:${version}
  """
}
def deployToK8s16(String version, String environment, String deployment, String repo) {
  sh """ 
    kubectl16 \
      --context=arn:aws:eks:us-east-1:813218302951:cluster/fecnxg-dev1 \
      --namespace=${environment} \
      set image deployment/${deployment} ${deployment}=813218302951.dkr.ecr.us-east-1.amazonaws.com/${repo}:${version}
  """
}


