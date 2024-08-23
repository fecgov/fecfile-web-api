import os
import resource
import logging
import random
import json
import math

from locust import between, task, TaskSet, user, events
import locust_data_generator

# seconds
TIMEOUT = 30  # seconds


SCHEDULES = ["A"]  # Further schedules to be implemented in the future

# Avoid "Too many open files" error
resource.setrlimit(resource.RLIMIT_NOFILE, (10000, 999999))


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


@events.init_command_line_parser.add_listener
def _(parser):
    parser.add_argument(
        "--username",
        type=str,
        env_var="LOCAL_TEST_USER",
        default="test@test.com",
        help="username for local testing",
    )
    parser.add_argument(
        "--password",
        type=str,
        env_var="LOCAL_TEST_PWD",
        help="password for local testing",
    )
    parser.add_argument(
        "--session-id",
        type=str,
        env_var="OIDC_SESSION_ID",
        help="session id for cloud.gov testing",
    )
    parser.add_argument(
        "--wanted-reports",
        type=int,
        env_var="LOCUST_WANTED_REPORTS",
        default=10,
        help="number of reports to create",
    )
    parser.add_argument(
        "--wanted-contacts",
        type=int,
        env_var="LOCUST_WANTED_CONTACTS",
        default=100,
        help="number of contacts to create",
    )
    parser.add_argument(
        "--wanted-transactions",
        type=int,
        env_var="LOCUST_WANTED_TRANSACTIONS",
        default=500,
        help="number of transactions to create",
    )
    parser.add_argument(
        "--transactions-single-to-triple-ratio",
        type=float,
        env_var="LOCUST_TRANSACTIONS_SINGLE_TO_TRIPLE_RATIO",
        default=9 / 10,
        help="ratio of single to triple transactions",
    )


class Tasks(TaskSet):
    report_ids = []
    contacts = []

    def on_start(self):
        parsed_options = self.environment.parsed_options
        if "cloud.gov" in self.client.base_url:
            self.client.headers = {
                "cookie": f"sessionid={parsed_options.session_id};",
                "user-agent": "Locust testing",
            }
            self.report_ids = self.fetch_values("reports", "id")
            self.contacts = self.scrape_endpoint("contacts")
        else:
            username = parsed_options.username
            password = parsed_options.password
            login_response = self.client.post(
                "/api/v1/user/login/authenticate",
                json={"username": username, "password": password},
            )
            csrftoken = login_response.cookies.get("csrftoken")
            self.client.headers = {"X-CSRFToken": csrftoken}
            committees = self.fetch_values("committees", "id")
            committee_uuid = committees[0]
            print("committee_uuid", committee_uuid)
            activate_response = self.client.post(
                f"/api/v1/committees/{committee_uuid}/activate/"
            )
            print("activate_response.status_code", activate_response.status_code)
            report_count = self.fetch_count("reports")
            contact_count = self.fetch_count("contacts")
            transaction_count = self.fetch_count("transactions")
            wanted_reports = parsed_options.wanted_reports
            if report_count < wanted_reports:
                logging.info("Not enough reports, creating some")
                self.create_reports(wanted_reports - report_count)
            wanted_contacts = parsed_options.wanted_contacts
            if contact_count < wanted_contacts:
                logging.info("Not enough contacts, creating some")
                self.create_contacts(wanted_contacts - contact_count)

            self.report_ids = self.fetch_values("reports", "id")
            logging.info(f"Report ids {self.report_ids}")
            self.contacts = self.scrape_endpoint("contacts")
            wanted_transactions = parsed_options.wanted_transactions
            single_to_triple_ratio = parsed_options.transactions_single_to_triple_ratio
            if transaction_count < wanted_transactions:
                logging.info("Not enough transactions, creating some")
                difference = wanted_transactions - transaction_count
                singles_needed = math.ceil(difference * single_to_triple_ratio)
                triples_needed = math.ceil(difference * (1 - single_to_triple_ratio))
                self.create_single_transactions(singles_needed)
                self.create_triple_transactions(triples_needed)

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
            results = response.json().get("results", [])
        while response.status_code == 200 and response.json()["next"] is not None:
            results += response.json().get("results", [])
            page += 1
            response = self.get_page(endpoint, page=page)

        return results

    def get_page(self, endpoint, page=1):
        params = {
            "page": page,
            "ordering": "form_type",
        }
        return self.client.get(
            f"/api/v1/{endpoint}", params=params, name=f"preload_{endpoint}_ids"
        )

    @task
    def celery_test(self):
        self.client.get("/celery-test/", name="celery-test", timeout=TIMEOUT)

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
    wait_time = between(1, 5)
