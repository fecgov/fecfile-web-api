#!/bin/bash

# magic StackOverflow one liner to get the dirname where the script lives
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

cd ${SCRIPT_DIR}/front-end

#clean enverything up so we get a fresh build
rm -rf dist node_modules

#create the docker we will use to perform the build
docker build -t fecfile-web-cf-build -f Dockerfile-cf-build .

#build the app 
docker run -v ${SCRIPT_DIR}/front-end/:/usr/src/app fecfile-web-cf-build sh -c 'cd /usr/src/app/ && npm install && node --max_old_space_size=4000 ./node_modules/\@angular/cli/bin/ng build'

#copy all the nginx and cloud foundry files into the Angualr dist dir
cp ${SCRIPT_DIR}/deploy-config/front-end-nginx-config/* ${SCRIPT_DIR}/front-end/dist
cd ${SCRIPT_DIR}/front-end/dist
cf push 
