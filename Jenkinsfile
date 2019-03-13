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
        stage("Build Images"){
          steps{
            // Build backend for dev environment
            imageBuild("${VERSION}","django-backend","fecnxg-django-backend",false)
            //Build frontEnd
            imageBuild("${VERSION}","front-end","fecnxg-frontend", "awsdev")
            //Build flyway Image 
            build_flyway("${VERSION}", "data","fecfile-flyway-db")
          }
        }
       
        stage("Deploy App"){
          steps{
            //Deploy flyway
            sh("bash data/deploy.sh ${VERSION} fecfile-frontend-dev-db.casvptvnuxni.us-east-1.rds.amazonaws.com dev ")
            //deployToK8s(String version, String environment, String deployment, String repo)
            //Deploy backend
            deployToK8s("${VERSION}", "dev","fecfile-backend-api","fecnxg-django-backend")
            //Deploy frontend
            deployToK8s("${VERSION}", "dev", "fecfile-frontend","fecnxg-frontend")
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
          steps{
            // Build backend for dev environment
            imageBuild("${VERSION}","django-backend","fecnxg-django-backend",false)
            //Build frontEnd
            imageBuild("${VERSION}","front-end","fecnxg-frontend", "awsqa")
            //Build flyway Image 
            build_flyway("${VERSION}", "data","fecfile-flyway-db")
          }
        }
       
        stage("Deploy App"){
          steps{
            //Deploy flyway
            sh("bash data/deploy.sh ${VERSION} fecfile-frontend-qa-db.casvptvnuxni.us-east-1.rds.amazonaws.com qa ")
            //deployToK8s(String version, String environment, String deployment, String repo)
            //Deploy backend
            deployToK8s("${VERSION}", "qa","fecfile-backend-api","fecnxg-django-backend")
            //Deploy frontend
            deployToK8s("${VERSION}", "qa", "fecfile-frontend","fecnxg-frontend")
          }
        }
      }
    }
    //End of qa stage 
    stage('UAT'){
      when { branch 'master'}
      stages {
        stage("Build Images"){
          steps{
            // Build backend for dev environment
            imageBuild("${VERSION}","django-backend","fecnxg-django-backend",false)
            //Build frontEnd
            imageBuild("${VERSION}","front-end","fecnxg-frontend", "awsuat")
            //Build flyway Image 
            build_flyway("${VERSION}", "data","fecfile-flyway-db")
          }
        }
       
        stage("Deploy App"){
          steps{
            //Deploy flyway
            sh("bash data/deploy.sh ${VERSION} fecfile-frontend-uat-db.casvptvnuxni.us-east-1.rds.amazonaws.com uat")
            //deployToK8s(String version, String environment, String deployment, String repo)
            //Deploy backend
            deployToK8s("${VERSION}", "uat","fecfile-backend-api","fecnxg-django-backend")
            //Deploy frontend
            deployToK8s("${VERSION}", "uat", "fecfile-frontend","fecnxg-frontend")
          }
        }
      }
    }
    //end of UAT stage
  }

  post {
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

def imageBuild(String version, String location, String repo, Boolean frontend_env) {
  if(frontend_env == "awsdev"){
    sh("sed -i 's/local/${fronend_env}/g ${location}/Dockerfile'")
  }
  if (frontend_env == "awsqa") {
    sh("sed -i 's/local/${fronend_env}/g ${location}/Dockerfile'")
    sh("sed -i 's/awsdev/${fronend_env}/g ${location}/Dockerfile'")
  }

  if (frontend_env == "awsuat") {
    sh("sed -i 's/local/${fronend_env}/g ${location}/Dockerfile'")
    sh("sed -i 's/awsdev/${fronend_env}/g ${location}/Dockerfile'")
    sh("sed -i 's/awsqa/${fronend_env}/g ${location}/Dockerfile'")
  }
 
  def imageB = docker.build("${repo}:${version}", "${location}")
  docker.withRegistry("https://813218302951.dkr.ecr.us-east-1.amazonaws.com/${repo}") {
    imageB.push();
  }
}

def build_flyway(String versin, String location, String repo) {
  sh("sed -i '11d' ${location}/flyway_migration.sh")
  imageBuild("${version}", "data", "fecfile-flyway-db", False )
}

def deployToK8s(String version, String environment, String deployment, String repo) {
  sh("kubectl --context=arn:aws:eks:us-east-1:813218302951:cluster/fecfile --namespace=${environment} set image deployment/${deployment} ${deployment}=813218302951.dkr.ecr.us-east-1.amazonaws.com/${repo}:${version} --dry-run=True")
}