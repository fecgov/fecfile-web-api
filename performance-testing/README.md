# Locust Testing

Locust testing is used to simulate swarms of users making requests to an API service, allowing
the testing of API performance under load.  Locust tests are first set up by spinning up a
docker container.  The user can then visit http://localhost:8089/ to start a testing session.

The instructions for running tests with Locust follow:

## (Optional) Prepare testing data

If you want a measure of consistency when testing with locust, you can pre-generate Contacts,
Reports, and Transactions for use in Locust testing.  These will be stored in .json files in
the locust-data subdirectory, with separate files for each resource (e.g, `contacts.locust.json`).
If the script finds .json files, locust testing will preferentially pull resources from them
before creating additional resources randomly as needed.  Inter-resource links (such as the
`contact_id` and `report_id` fields on a transaction) are not pre-generated and are instead
determined randomly at run-time.

You can generate these .json files by running `python performance-testing/locust_data_generator.py`
Run the script with the `-h` flag for additional information.

## Setup - Environment variables

- `LOCAL_TEST_USER`
  - Committee ID concatenated with email
- `LOCAL_TEST_PWD`
  - The password corresponding to the user data in the preceeding variable
- `LOCUST_WANTED_REPORTS` (Optional. Default: 10)
  - Determines the number of Report records stored in the API before running locust tasks
- `LOCUST_WANTED_CONTACTS` (Optional. Default: 100)
  - Determines the number of Contact records stored in the API before running locust tasks
- `LOCUST_WANTED_TRANSACTIONS` (Optional. Default: 500)
  - Determines the number of Transaction records stored in the API before running locust tasks
- `LOCUST_TRANSACTIONS_SINGLE_TO_TRIPLE_RATIO` (Optional. Default: 9 / 10)
  - Determines the proportion of transactions that will be created as single transactions
 (having no children) vs. triple transactions (with child and grandchild transactions)


## Setup - Additional steps for remote testing

1. Set an additional environment variable:
- `OIDC_SESSION_ID`
  - Used to log locust followers into the remote testing environment as part of testing
  - You can get the value for this by logging into the desired testing environment with cloud.gov
 and retrieving the session ID from any subsequent request header.

2. Set the target API service for testing in [docker-compose.yml](https://github.com/fecgov/fecfile-web-api/blob/develop/docker-compose.yml#L118):
- As an example, this is what you would set in order to target DEV:
  - `-f /mnt/locust/locust_run.py --master -H https://fecfile-web-api-dev.app.cloud.gov`

## Running Tests

1. Run the command `docker-compose --profile locust up` to spin up the testing environment
- (Optional) Scale up using docker by adding `--scale locust-follower=4` to the end

2. Go to http://localhost:8089/ in your browser of choice to run tests.

### Recommended tests:
- 5 users / 1 ramp-up rate
- 100 users / 1 ramp-up rate
- 500 users / 5 ramp-up rate

Advanced settings: Run time 5m

# How our Locust Testing works under the hood

When you start a test run from your browser, the testing that follows takes part in two phases:
Setup and Tasks.  Setup runs once at the start, and then Tasks run on loop for the duration of the
testing (if specified).

## Setup

The Setup phase has two jobs: logging in to the target API and preparing data before testing.

### Log In

Logging in locally works with a simple request to the API using the legacy debug login.  When testing
against a remote service, Locust doesn't actually log in.  Instead, Locust uses the session ID stored
in the `OIDC_SESSION_ID` env variable, using a session that you manually created rather than automating
the log in process.  This is needed because Login.gov uses two-factor authentication that cannot be
automated at this time.

### Preparing Data

Locust (or more accurately *our* Locust setup) needs a bevy of Contacts, Resources, and Transactions to
load test with.  Locust wants a specific number of Contact, Report, and Transaction records on the API
prior to beginning the Tasks phase.  These numbers can optionally be controlled with environment variables
specified above.

Once Locust knows how many records it wants, it makes requests against the API to determine the number of
records already present on the server (for the logged in committee).  If there aren't as many records as it
wants, Locust will make requests to create new records.  The data for these additional records will be taken
from .json files in the "/locust-data" subdirectory in order of appearance within each file.  If no .json
file is found or if not enough records are provided, the remaining records will be generated at random.
Each additional record is then submitted to the API.

## Tasks

The Task phase consists of swarm followers running functions tagged with the `@task` decorator on-loop for
the duration of the testing session.  There are (as of writing) four tasks:
- Celery Test
- Load Contacts
- Load Reports
- Load Transactions


# Silk Profiling

In addition to load testing, Silk query profiling can be installed to inspect queries and response times.

Installation instructions for local development can be found [here](https://github.com/jazzband/django-silk?tab=readme-ov-file#installation).
