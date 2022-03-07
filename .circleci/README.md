# CircleCI Configuration
## Environment Variables
When configuring CircleCI, you will need to set environment variables the database
configuration as follows:
```
DATABASE_URL = "postgres://postgres:postgres@0.0.0.0/postgres"
FECFILE_TEST_DB_NAME = "postgres"
FECFILE_FEC_WEBSITE_API_KEY="DEMO_KEY"
```
Notes:

CircleCI will attempt to deploy commits made to specific branches:
* branch __develop__ -> cloud.gov dev space
* branch __release__* (any branch starting with release) -> cloud.gov staging space
* branch __prod__ -> cloud.gov prod space

Authentication must be configured in a set of evironment variables:
* $FEC_CF_USERNAME_DEV
* $FEC_CF_PASSWORD_DEV
* $FEC_CF_USERNAME_STAGE
* $FEC_CF_PASSWORD_STAGE
* $FEC_CF_USERNAME_PROD
* $FEC_CF_PASSWORD_PROD

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

## Necessary Environment Variables
The Django backend expects to find the database login info in the environment.
To run in the local CircleCI for the django unit tests (for example), use the following:

```
circleci local execute -e DATABASE_URL=${DATABASE_URL} \
         -e FECFILE_FEC_WEBSITE_API_KEY=${FECFILE_FEC_WEBSITE_API_KEY} \
         -e FECFILE_TEST_DB_NAME=${FECFILE_TEST_DB_NAME} \
         --job test
```

## CircleCI configuration
To get CircleCI to run tests, you have to configure the
project in the Circle web applicaiton https://app.circleci.com/
