import os
import logging
import random
import json
import math

from locust import between, task, TaskSet, user
import locust_data_generator


TEST_USER = os.environ.get("LOCAL_TEST_USER")
TEST_PWD = os.environ.get("LOCAL_TEST_PWD")
SESSION_ID = os.environ.get("OIDC_SESSION_ID")
CSRF_TOKEN = os.environ.get("CSRF_TOKEN")

# seconds
TIMEOUT = 30  # seconds

# item counts
WANTED_REPORTS = int(os.environ.get("LOCUST_WANTED_REPORTS", 10))
WANTED_CONTACTS = int(os.environ.get("LOCUST_WANTED_CONTACTS", 100))
WANTED_TRANSACTIONS = int(os.environ.get("LOCUST_WANTED_TRANSACTIONS", 500))
SINGLE_TO_TRIPLE_RATIO = float(
    os.environ.get("LOCUST_TRANSACTIONS_SINGLE_TO_TRIPLE_RATIO", 9 / 10)
)

SCHEDULES = ["A"]  # Further schedules to be implemented in the future


def get_json_data(name):
    directory = os.path.dirname(os.path.abspath(__file__))
    filename = f"{name}.locust.json"
    full_filename = os.path.join(directory, "locust-data", filename)
    if os.path.isfile(full_filename):
        try:
            file = open(full_filename, "r")
            values = json.loads(file.read())
            file.close()
            logging.info(f"Retrieved {len(values)} items from {filename}")
            return values
        except (IOError, ValueError):
            logging.error(f"Unable to retrieve locust data from file {filename}")

    return []


class Tasks(TaskSet):
    report_ids = []
    contacts = []

    def on_start(self):
        if "fec.gov" in self.client.base_url:
            self.client.headers = {
                "cookie": f"sessionid={SESSION_ID}; csrftoken={CSRF_TOKEN};",
                "user-agent": "Locust testing",
                "x-csrftoken": CSRF_TOKEN,
                "Origin": self.client.base_url,
            }
        else:
            self.login_via_mock_oidc()

        committees = self.fetch_values("committees", "id")
        committee_uuid = committees[0]
        activate_response = self.client.post(
            f"api/v1/committees/{committee_uuid}/activate/",
            headers=self.client.headers
        )

        if activate_response.status_code != 200:
            return

        report_count = self.fetch_count("reports")
        contact_count = self.fetch_count("contacts")
        transaction_count = self.fetch_count("transactions")
        if report_count < WANTED_REPORTS:
            logging.info("Not enough reports, creating some")
            self.create_reports(WANTED_REPORTS - report_count)
        if contact_count < WANTED_CONTACTS:
            logging.info("Not enough contacts, creating some")
            self.create_contacts(WANTED_CONTACTS - contact_count)

        self.report_ids = self.fetch_values("reports", "id")
        logging.info(f"Report ids {self.report_ids}")
        self.contacts = self.scrape_endpoint("contacts")
        if transaction_count < WANTED_TRANSACTIONS:
            logging.info("Not enough transactions, creating some")
            difference = WANTED_TRANSACTIONS - transaction_count
            singles_needed = math.ceil(difference * SINGLE_TO_TRIPLE_RATIO)
            triples_needed = math.ceil(difference * (1 - SINGLE_TO_TRIPLE_RATIO))
            self.create_single_transactions(singles_needed)
            self.create_triple_transactions(triples_needed)

    def login_via_mock_oidc(self):
        authenticate_response = self.client.get(
            "/api/v1/oidc/authenticate/", allow_redirects=False
        )
        authorize_response = self.client.get(
            authenticate_response._next.url.removeprefix("http://localhost:8080"),
            allow_redirects=False,
        )
        callback_response = self.client.get(
            authorize_response._next.url,
            allow_redirects=False,
        )
        csrftoken = callback_response.cookies.get("csrftoken")
        self.client.headers = {"X-CSRFToken": csrftoken}

    def create_reports(self, count=1):
        fields_to_validate = [
            "filing_frequency",
            "report_type_category",
            "report_code",
            "coverage_from_date",
            "coverage_through_date",
            "date_of_election",
            "state_of_election",
            "form_type",
        ]
        params = {"fields_to_validate": fields_to_validate}

        reports = get_json_data("form-3x")
        if len(reports) < count:
            reports = locust_data_generator.generate_form_3x(count - len(reports))

        for report in reports[:count]:
            self.client.post(
                "/api/v1/reports/form-3x/",
                name="create_report",
                # TODO: does it make sense to pass both the params and json here?
                params=params,
                json=report,
            )

    def create_contacts(self, count=1):
        contacts = get_json_data("contacts")
        if len(contacts) < count:
            contacts += locust_data_generator.generate_contacts(count - len(contacts))

        for contact in contacts[:count]:
            self.client.post(
                "/api/v1/contacts/",
                name="create_contacts",
                # TODO: does it make sense to pass both the params and json here?
                # Same with create_reports
                json=contact,
                timeout=TIMEOUT,
            )

    def create_single_transactions(self, count=1):
        transactions = get_json_data("single-transactions")
        self.patch_prebuilt_transactions(transactions)
        if len(transactions) < count:
            difference = count - len(transactions)
            transactions += locust_data_generator.generate_single_transactions(
                difference, self.contacts, self.report_ids
            )

        for transaction in transactions[:count]:
            self.create_transaction(transaction)

    def create_triple_transactions(self, count=1):
        transactions = get_json_data("triple-transactions")
        self.patch_prebuilt_transactions(transactions)
        if len(transactions) < count:
            difference = count - len(transactions)
            transactions += locust_data_generator.generate_triple_transactions(
                difference, self.contacts, self.report_ids
            )

        for transaction in transactions[:count]:
            self.create_transaction(transaction)

    def patch_prebuilt_transactions(self, transactions):
        for t in transactions:
            report_id = random.choice(self.report_ids)

            t["report_ids"] = [report_id]
            t["contact_1_id"] = random.choice(self.contacts)["id"]

            for child in t["children"]:
                child["report_ids"] = [report_id]
                child["contact_1_id"] = random.choice(self.contacts)["id"]
                for grandchild in child["children"]:
                    grandchild["report_ids"] = [report_id]
                    grandchild["contact_1_id"] = random.choice(self.contacts)["id"]

    def create_transaction(self, transaction):
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
            "reattribution_redesignation_tag",
        ]
        params = {"fields_to_validate": fields_to_validate}
        self.client.post(
            "/api/v1/transactions/",
            name="create_transactions",
            params=params,
            json=transaction,
            timeout=TIMEOUT,
        )

    def fetch_count(self, endpoint):
        response = self.get_page(endpoint)
        return response.json()["count"]

    def fetch_values(self, endpoint, key):
        values = []
        results = self.scrape_endpoint(endpoint)
        for result in results:
            value = result.get(key, None)
            if value is not None:
                values.append(value)

        return values

    def scrape_endpoint(self, endpoint):
        results = []
        page = 1
        response = self.get_page(endpoint)
        if response.status_code == 200:
            json = response.json()
            results = json.get("results", [])
        while response.status_code == 200 and response.json()["next"] is not None:
            results += response.json().get("results", [])
            page += 1
            response = self.get_page(endpoint, page=page)

        return results

    def get_page(self, endpoint, page=1):
        params = {
            "page": page,
        }
        return self.client.get(
            f"/api/v1/{endpoint}/", params=params, name=f"preload_{endpoint}_ids"
        )

    @task
    def celery_test(self):
        self.client.get("/devops/celery-status/", name="celery-status", timeout=TIMEOUT)

    @task
    def load_contacts(self):
        params = {
            "page": 1,
            "ordering": "form_type",
        }
        self.client.get(
            "/api/v1/contacts/", name="load_contacts", timeout=TIMEOUT, params=params
        )

    @task
    def load_reports(self):
        params = {
            "page": 1,
            "ordering": "form_type",
        }
        self.client.get(
            "/api/v1/reports/", name="load_reports", timeout=TIMEOUT, params=params
        )

    @task
    def load_transactions(self):
        if len(self.report_ids) > 0:
            report_id = random.choice(self.report_ids)
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
                timeout=TIMEOUT,
                params=params,
            )


class Swarm(user.HttpUser):
    tasks = [Tasks]
    wait_time = between(1.5, 4)
