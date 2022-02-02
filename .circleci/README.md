# CircleCI Configuration
## Environment Variables
When configuring CircleCI, you will need to set environment variables the database
configuration as follows:
```
DATABASE_URL = "postgres://postgres:postgres@0.0.0.0/postgres"
FECFILE_FEC_WEBSITE_API_KEY=
```
Notes:
* There is no default FECFILE_FEC_WEBSITE_API_KEY, you must obtain and set this yourself
* The FECFILE_DB_HOST value here is different than what you need for your local docker-compose configuration.

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
         -e FECFILE_FEC_WEBSITE_API_KEY=${FECFILE_FEC_WEBSITE_API_KEY}\
         --job unit-test
```

## CircleCI configuration
To get CircleCI to run tests, you have to configure the
project in the Circle web applicaiton https://app.circleci.com/
