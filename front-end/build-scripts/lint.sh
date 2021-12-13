#!/bin/bash

# you should run this from the
# magic StackOverflow one liner to get the dirname where the script lives
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"


rm -rf docker-build-tmp
mkdir -p docker-build-tmp
cp build-scripts/Dockerfile-lint docker-build-tmp/Dockerfile-lint
cd docker-build-tmp
docker build -t fecfile-lint -f Dockerfile-lint .
rm -rf docker-build-tmp
echo run
docker run -v ${SCRIPT_DIR}/:/usr/src/app fecfile-lint sh -c 'cd /usr/src/app && eslint "src/**" || echo BAD NEWS: LINT ERRORS FOUND'

