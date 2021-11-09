#!/bin/bash

# magic StackOverflow one liner to get the dirname where the script lives
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

cd ${SCRIPT_DIR}/front-end
rm -rf dist node_modules
docker build -t fecfile-web-cf-build -f Dockerfile-cf-build .

docker run -v ${SCRIPT_DIR}/front-end/:/usr/src/app fecfile-web-cf-build sh -c 'cd /usr/src/app/ && npm install && node --max_old_space_size=4000 ./node_modules/\@angular/cli/bin/ng build'

echo cf push -f frontend-manifest
