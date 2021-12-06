# Using CircleCI local CLI 

## Install circleci local
Install on Linux or Mac with:
```
curl -fLSs https://raw.githubusercontent.com/CircleCI-Public/circleci-cli/master/install.sh | bash
```

Details and instructions for other platforms in the [CircleCI Docs](https://circleci.com/docs/2.0/local-cli/)

## Validate the config.yml
Run this from the top level of the repo:
```
circleci config validate
```

## Run the CircleCI Job locally
You can run a CircleCI job locally and avoid the change/commit/wait loop you need to 
do if you want to actually run the changes on Circle. 
This can save a lot of time when trying to debug an issue in CI.
```
circleci local execute --job JOB_NAME
```

## CircleCI configuration
To get CircleCI to run tests, you have to configure the
project in the Circle web applicaiton https://app.circleci.com/