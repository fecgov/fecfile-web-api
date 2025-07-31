# Quick Start

1. Run the following data load management command in the environment to test against
   using the user email address you wish to be assigned to the new committee (optional
   additional command arguments as desired):
   `./manage.py gen_locust_load_test_data <user_email>`
2. Run Locust locally using the following command (you may not need `sudo`):
   `sudo docker compose --profile locust up`
3. Open a browser to http://localhost:8089 and begin testing.
4. Once you are done testing, you may wish to cleanup the load test data created in step
   3 using the following management command (committee `C33333333` is the default used):
   `./manage.py delete_committee_account <committee_account_id>`

# Locust Testing detailed instructions

Locust testing is used to simulate swarms of users making requests to an API service, allowing
the testing of API performance under load.  Locust tests are first set up by spinning up a
docker container.  The user can then visit http://localhost:8089/ to start a testing session.

The instructions for running tests with Locust follow:

## (Optional) Prepare testing data with gen_locust_load_test_data command

A new devops command has been added to insert test data directly into the database.  This
command can be executed as follows using the user_email you wish to be assigned to the
new commmittee.  By default, the committees created will start with C33333333 and count
upwards:

`python manage.py gen_locust_load_test_data <user_email>`

Optional additional flags can be used to override various defaults:

`--base_uri`
`--number_of_committees`
`--number_of_reports`
`--number_of_contacts`
`--number_of_transactions`
`--single_to_triple_transaction_ratio`


## Setup - Additional steps for remote testing

1. Set an additional environment variables:
- Set the target API service for testing in [docker-compose.yml](https://github.com/fecgov/fecfile-web-api/blob/develop/docker-compose.yml#L118):
- As an example, this is what you would set in order to target DEV:
  - `-f /mnt/locust/locust_run.py --master -H https://dev-api.fecfile.fec.gov`

## Running Tests

1. Run the command `docker compose --profile locust up -d` to spin up the testing environment
- (Optional) Scale up using docker by adding `--scale locust-follower=4` to the end
- You also may need to use the --force-recreate flag

2. Go to http://localhost:8089/ in your browser of choice to run tests.

3. If testing locally, set Host to http://fecfile-api-proxy:8080

### Recommended tests:
- 5 users / 1 ramp-up rate
- 100 users / 1 ramp-up rate
- 500 users / 5 ramp-up rate

Advanced settings: Run time 5m

# How our Locust Testing works under the hood

When you start a test run from your browser, the testing that follows takes part in two phases:
Setup and Tasks.  Setup runs once at the start of each thread, and then Tasks run on loop for
the duration of the testing (if specified).

## Setup

The setup for each thread consists of retrieving a list of report_ids to be used throughout
the testing tasks.  It also selects a subset of these report ids to submit depending on the
number of threads (users) configured for the test run.  It then prepares these report ids
for submission (which takes place as in a load testing task)


## Tasks

The Task phase consists of swarm followers running functions tagged with the `@task` decorator on-loop for
the duration of the testing session.  There are (as of writing) five tasks:
- Celery Test
- Load Contacts
- Load Reports
- Load Transactions
- Submit report


# Silk Profiling

In addition to load testing, Silk query profiling can be installed to inspect queries and response times.

For a jump-start in setting up for Silk testing, consider merging in the `silk-profiling-base` branch.
The branch contains the necessary configuration changes and marks a selection of functions for profiling.
Silk requires changes to the database, so after merging, be sure to run `python manage.py migrate`
or spin up a fresh container.

Once set up, silk profiling will run automatically as the API receives and processes requests.
To view the results, visit the API's `/silk` endpoint (for local development: `localhost:8080/silk/`)

If setting up from scratch or looking for usage instructions, you can find documentation [here](https://github.com/jazzband/django-silk?tab=readme-ov-file#installation).


# Creating and loading bulk data with fixtures

Fixtures are .json files that can be used to load data into the database.  Loading data with fixtures is far faster than
creating records with individual requests, making it especially useful for preparing a database for ad-hoc performance testing.

A script has been provided for generating fixtures with specific numbers of records.  You can run the script with
```
  python bulk-testing-data-fixture-generator.py
```
The script requires an environment variable to function:
- `LOCAL_TEST_COMMITTEE_UUID`: Used to ensure that created records are viewable within the test committee.
For most cases, the value in the `e2e-test-data.json` fixture is what you're looking for.  This can be overriden
by using the `--committee-uuid` optional parameter when running the script.

Running the script with the `-h` or `--help` flags will provide additional information.

Once you have a fixture, you can load it into the database by following these steps:

1. Enter a fecfile-api docker container
- (For Local) Use `docker exec -it fecfile-api /bin/bash`
- (For Cloud.gov or Circle CI) ssh into your docker instance of choice.
2. (Cloud.gov only) use `/tmp/lifecycle/shell` to establish a shell session.
3. Run `python manage.py loaddata FIXTURE-NAME` to load your fixture.
