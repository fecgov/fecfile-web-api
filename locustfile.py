"""Load testing for the FECFile API and web app. Run from command directory using the

*Run tests locally:*
Environment variables:
Ask team about what to set for
`LOCAL_TEST_USER` and `LOCAL_TEST_PWD`

`docker-compose --profile locust up -d`

Go to http://0.0.0.0:8089/ to run tests.

Recommended tests:
5 users / 1 ramp-up rate
100 users / 1 ramp-up rate
500 users / 5 ramp-up rate

Advanced settings: Run time 5m

*Run tests on other spaces:*
Log in to that environment, and get the session ID from the header and update the
OIDC_SESSION_ID environment variable on your local machine

Modifying docker-compose:
-f /mnt/locust/locustfile.py --master -H https://fecfile-web-api-dev.app.cloud.gov

Scale up using docker:
docker-compose --profile locust up -d --scale locust-follower=4

Go to http://0.0.0.0:8089/ to run tests.

"""

import os
import resource
import logging
import random

from locust import between, task, TaskSet, user

TEST_USER = os.environ.get("LOCAL_TEST_USER")
TEST_PWD = os.environ.get("LOCAL_TEST_PWD")
SESSION_ID = os.environ.get("OIDC_SESSION_ID")

SCHEDULES = ["A", "B,E", "C,D"]
REPORTS_AND_DATES = [
    {
        "report_code": "Q1",
        "coverage_from_date": "{}-01-01",
        "coverage_through_date": "{}-03-31",
    },
    {
        "report_code": "Q2",
        "coverage_from_date": "{}-04-01",
        "coverage_through_date": "{}-06-30",
    },
    {
        "report_code": "Q3",
        "coverage_from_date": "{}-07-01",
        "coverage_through_date": "{}-09-30",
    },
    {
        "report_code": "Q4",
        "coverage_from_date": "{}-10-01",
        "coverage_through_date": "{}-12-31",
    }
]

# seconds
timeout = 30  # seconds

# Avoid "Too many open files" error
resource.setrlimit(resource.RLIMIT_NOFILE, (10000, 999999))


def generate_random_report():
    """This isn't that many different combinations - could still have some clashes"""
    report = random.choice(REPORTS_AND_DATES)
    year = random.choice(range(1800, 4040))
    report["coverage_from_date"] = report["coverage_from_date"].format(year)
    report["coverage_through_date"] = report["coverage_through_date"].format(year)
    return report


class Tasks(TaskSet):

    def on_start(self):
        if "cloud.gov" in self.client.base_url:
            self.client.headers = {
                "cookie": f"sessionid={SESSION_ID};",
                "user-agent": "Locust testing",
            }
        else:
            login_response = self.client.post(
                "/api/v1/user/login/authenticate",
                json={"username": TEST_USER, "password": TEST_PWD}
            )
            csrftoken = login_response.cookies.get('csrftoken')
            self.client.headers = {
                "X-CSRFToken": csrftoken
            }
            committees = self.fetch_ids("committees", "id")
            committee_uuid = committees[0]
            print("committee_uuid", committee_uuid)
            activate_response = self.client.post(
                f"/api/v1/committees/{committee_uuid}/activate/"
            )
            print("activate_response.status_code", activate_response.status_code)
            if len(self.fetch_ids("reports", "id")) < 10:
                logging.info("Not enough reports, creating some")
                self.create_report()
            if len(self.fetch_ids("transactions", "id")) < 10:
                logging.info("Not enough transactions, creating some")
                self.create_transaction()
            self.create_contact()

        self.reports = self.fetch_ids("reports", "id")
        self.contacts = self.fetch_ids("contacts", "id")

    def create_report(self):
        report = generate_random_report()
        fields_to_validate = [
            "filing_frequency",
            "report_type_category",
            "report_code",
            "coverage_from_date",
            "coverage_through_date",
            "date_of_election",
            "state_of_election",
            "form_type"
        ]
        params = {
            "fields_to_validate": fields_to_validate
        }
        json = {
            "hasChangeOfAddress": "true",
            "submitAlertText": "Are you sure you want to submit this form \
                electronically? Please note that you cannot undo this action. \
                Any changes needed will need to be filed as an amended report.",
            "report_type": "F3X",
            "form_type": "F3XN",
            "report_code": report.get("report_code"),
            "date_of_election": None,
            "state_of_election": None,
            "coverage_from_date": report.get("coverage_from_date"),
            "coverage_through_date": report.get("coverage_through_date")
        }
        self.client.post(
            "/api/v1/reports/form-3x/",
            name="create_report",
            # TODO: does it make sense to pass both the params and json here?
            params=params,
            json=json
        )

    def create_contact(self):
        json = {
            "type": "IND",
            "street_1": "123 Main St",
            "city": "Washington",
            "state": "AL",
            "zip": "20000",
            "country": "USA",
            "last_name": "Business",
            "first_name": "Mrs",
            "middle_name": None,
            "prefix": None,
            "suffix": None,
            "street_2": None,
            "telephone": None,
            "employer": None,
            "occupation": None
        }
        self.client.post(
            "/api/v1/contacts/",
            name="create_contacts",
            # TODO: does it make sense to pass both the params and json here?
            # Same with create_reports
            json=json,
            timeout=timeout
        )

    def create_transaction(self):
        contact_id = random.choice(self.contacts)
        fields_to_validate = [
            "form_type",
            "transaction_type_identifier",
            "entity_type",
            "contributor_last_name",
            "contributor_first_name",
            "contributor_middle_name",
            "contributor_prefix",
            "contributor_suffix",
            "contributor_street_1",
            "contributor_street_2",
            "contributor_city",
            "contributor_state",
            "contributor_zip",
            "contribution_date",
            "contribution_amount",
            "contribution_aggregate",
            "aggregation_group",
            "contribution_purpose_descrip",
            "contributor_employer",
            "contributor_occupation",
            "memo_code",
            "memo_text_description",
            "reattribution_redesignation_tag"
        ]
        params = {
            "fields_to_validate": fields_to_validate
        }
        json = {
            "children": [],
            "form_type": "SA11AI",
            "transaction_type_identifier": "INDIVIDUAL_RECEIPT",
            "aggregation_group": "GENERAL",
            "contact_1_id": contact_id,
            "schema_name": "INDIVIDUAL_RECEIPT",
            # "fields_to_validate":
            "report_id": random.choice(self.reports),
            # "contact_1": {
            #     "type": "IND",
            #     "street_1": "11 A St NW Apt 3",
            #     "city": "Washington",
            #     "state": "AL",
            #     "zip": "20000",
            #     "country": "USA",
            #     "deleted": None,
            #     "committee_account_id": "9fa4aa10-b993-4bbf-8eee-e7973c9d87b8",
            #     "id": contact_id,
            #     "candidate_id": None,
            #     "committee_id": None,
            #     "name": None,
            #     "last_name": "Business",
            #     "first_name": "Nunya",
            #     "middle_name": None,
            #     "prefix": None,
            #     "suffix": None,
            #     "street_2": None,
            #     "employer": "Business",
            #     "occupation": "Business",
            #     "candidate_office": None,
            #     "candidate_state": None,
            #     "candidate_district": None,
            #     "telephone": None,
            #     "created": "2024-02-08T19:05:15.925Z",
            #     "updated": "2024-02-08T19:05:15.925Z",
            #     "transaction_count": 9,
            #     "full_name_fwd": "nunya business",
            #     "full_name_bwd": "business nunya"
            # },
            "entity_type": "IND",
            "contributor_last_name": "Business",
            "contributor_first_name": "Nunya",
            "contributor_middle_name": None,
            "contributor_prefix": None,
            "contributor_suffix": None,
            "contributor_street_1": "11 A St NW",
            "contributor_street_2": None,
            "contributor_city": "Washington",
            "contributor_state": "AL",
            "contributor_zip": "20000",
            "contribution_date": "2024-02-01",
            "contribution_amount": 1234,
            "contribution_aggregate": 102200,
            "contribution_purpose_descrip": None,
            "contributor_employer": "Business",
            "contributor_occupation": "Business",
            "memo_code": None,
            "date": None,
            "amount": None,
            "purpose_description": None,
            "text4000": None,
            "street_1": None,
            "street_2": None,
            "city": None,
            "state": None,
            "zip": None,
            "aggregate": None,
            "last_name": None,
            "first_name": None,
            "middle_name": None,
            "prefix": None,
            "suffix": None,
            "employer": None,
            "occupation": None,
            "schedule_id": "A"
        }
        self.client.post(
            "/api/v1/transactions/",
            name="create_transactions",
            params=params,
            json=json,
            timeout=timeout
        )

    def fetch_ids(self, endpoint, key):
        response = self.client.get(f"/api/v1/{endpoint}", name=f"preload_{endpoint}_ids")
        if response.status_code == 200:
            return [result[key] for result in response.json()["results"]]
        else:
            logging.error(f"{response.status_code} error fetching pre-load id")

    @task
    def celery_test(self):
        self.client.get(
            "/celery-test/",
            name="celery-test",
            timeout=timeout
        )

    @task
    def load_contacts(self):
        params = {
            "page": 1,
            "ordering": "form_type",
        }
        self.client.get(
            "/api/v1/contacts/",
            name="load_contacts",
            timeout=timeout,
            params=params
        )

    @task
    def load_reports(self):
        params = {
            "page": 1,
            "ordering": "form_type",
        }
        self.client.get(
            "/api/v1/reports/",
            name="load_reports",
            timeout=timeout,
            params=params
        )

    @task
    def load_transactions(self):
        report_id = random.choice(self.reports)
        schedules = random.choice(SCHEDULES)
        params = {
            "page": 1,
            "ordering": "form_type",
            "schedules": schedules,
            "report_id": report_id,
        }
        self.client.get(
            "/api/v1/transactions/",
            name="load_transactions",
            timeout=timeout,
            params=params
        )


class Swarm(user.HttpUser):
    tasks = [Tasks]
    wait_time = between(1, 5)
