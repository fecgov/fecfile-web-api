import os
import logging
import random
import json
import math
import time
import threading

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
            f"/api/v1/committees/{committee_uuid}/activate/", headers=self.client.headers
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

        report_id_and_coverage_from_date_list = (
            self.retrieve_report_id_and_coverage_from_date_list()
        )
        self.report_ids = list(report_id_and_coverage_from_date_list.keys())

        logging.info(f"Report ids {self.report_ids}")
        self.contacts = self.scrape_endpoint("contacts")
        if transaction_count < WANTED_TRANSACTIONS:
            logging.info("Not enough transactions, creating some")
            difference = WANTED_TRANSACTIONS - transaction_count
            singles_needed = math.ceil(difference * SINGLE_TO_TRIPLE_RATIO)
            triples_needed = math.ceil(difference * (1 - SINGLE_TO_TRIPLE_RATIO))
            self.create_single_transactions(
                report_id_and_coverage_from_date_list,
                singles_needed,
            )
            self.create_triple_transactions(
                report_id_and_coverage_from_date_list, triples_needed
            )

        logging.info("Preparing reports for submit")
        self.prepared_reports_for_submit = self.prepare_reports_for_submit()
        self.report_ids_to_submit = self.report_ids.copy()
        self.report_ids_to_submit_lock = threading.Lock()

    def login_via_mock_oidc(self):
        authenticate_response = self.client.get(
            "/api/v1/oidc/authenticate", allow_redirects=False
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
                json=contact,
                timeout=TIMEOUT,
            )

    def create_single_transactions(self, report_id_and_coverage_from_date_list, count=1):
        transactions = get_json_data("single-transactions")
        self.patch_prebuilt_transactions(transactions)
        if len(transactions) < count:
            difference = count - len(transactions)
            transactions += locust_data_generator.generate_single_transactions(
                difference,
                self.contacts,
                report_id_and_coverage_from_date_list,
            )

        for transaction in transactions[:count]:
            self.create_transaction(transaction)

    def create_triple_transactions(self, report_id_and_coverage_from_date_list, count=1):
        transactions = get_json_data("triple-transactions")
        self.patch_prebuilt_transactions(transactions)
        if len(transactions) < count:
            difference = count - len(transactions)
            transactions += locust_data_generator.generate_triple_transactions(
                difference,
                self.contacts,
                report_id_and_coverage_from_date_list,
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
        return self.client_get(
            f"/api/v1/{endpoint}/", params=params, name=f"preload_{endpoint}_ids"
        )

    def prepare_reports_for_submit(self):
        logging.info("Calculating summaries for reports")
        report_json_list = self.calculate_summary_for_report_id_list(self.report_ids)
        logging.info("Confirming information for reports")
        return self.confirm_information_for_report_json_list(report_json_list)

    def calculate_summary_for_report_id_list(self, report_id_list):
        retval = []
        for report_id in report_id_list:
            try:
                retval.append(self.calculate_summary_for_report_id(report_id))
            except Exception as e:
                print(f"Error calculating summary for report_id {report_id}: {e}")
        return retval

    def calculate_summary_for_report_id(self, report_id, poll_seconds=2):
        response = self.client.post(
            "/api/v1/web-services/summary/calculate-summary/",
            name="calculate_report_summary",
            json={"report_id": report_id},
        )
        if response.status_code != 200:
            raise Exception("Failed to create calculate-summary task")
        for i in range(3):
            time.sleep(poll_seconds)
            report_json = self.retrieve_report(report_id)
            if report_json.get("calculation_status", None) == "SUCCEEDED":
                return report_json
        raise Exception("Failed to receive successful summary calculation status")

    def confirm_information_for_report_json_list(self, report_json_list):
        retval = []
        for report_json in report_json_list:
            try:
                retval.append(self.confirm_information_for_report_json(report_json))
            except Exception as e:
                print(f"Failed to confirm report information for {report_json}: {e}")
        return retval

    def confirm_information_for_report_json(self, report_json):
        fields_to_validate = [
            "confirmation_email_1",
            "confirmation_email_2",
            "change_of_address",
            "street_1",
            "street_2",
            "city",
            "state",
            "zip",
        ]
        params = {"fields_to_validate": fields_to_validate}
        report_id = report_json.get("id", None)
        if not report_id:
            raise Exception("Report JSON does not contain an id")
        report_json["confirmation_email_1"] = "test@test.com"
        report_json["hasChangeOfAddress"] = False
        response = self.client.put(
            f"/api/v1/reports/form-3x/{report_id}/",
            name="confirm_report_info_for_submit",
            params=params,
            json=report_json,
        )
        if response.status_code != 200:
            raise Exception("Failed to update/confirm report information")
        return self.retrieve_report(report_id)

    def submit_report(self, report_id, poll_seconds):
        self.update_report_for_submit(report_id)
        self.submit_to_fec_and_poll_for_success(report_id, poll_seconds)

    def update_report_for_submit(self, report_id):
        fields_to_validate = [
            "treasurer_first_name",
            "treasurer_last_name",
            "treasurer_middle_name",
            "treasurer_prefix",
            "treasurer_suffix",
            "filingPassword",
            "userCertified",
        ]
        params = {"fields_to_validate": fields_to_validate}
        report_json = self.retrieve_report(report_id)
        report_json["treasurer_last_name"] = "test_treasurer_last_name"
        report_json["treasurer_first_name"] = "test_treasurer_first_name"
        response = self.client.put(
            f"/api/v1/reports/form-3x/{report_id}/",
            name="update_report_treasurer_for_submit",
            params=params,
            json=report_json,
        )
        if response.status_code != 200:
            raise Exception("Failed to update report information for submit")

    def submit_to_fec_and_poll_for_success(self, report_id, poll_seconds=2):
        with self.client.post(
            "/api/v1/web-services/submit-to-fec/",
            name="submit_report_to_fec",
            json={"report_id": report_id, "password": "fake_pd"},
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure("Failed to post submit to fec task")
            for i in range(3):
                time.sleep(poll_seconds)
                report_json = self.retrieve_report(report_id)
                upload_submission = report_json.get("upload_submission", None)
                if (
                    upload_submission
                    and upload_submission.get("fec_status", None) == "ACCEPTED"
                ):
                    return report_json
            response.failure(
                f"Failed to get successful fec submit status for report_id {report_id}"
            )

    def retrieve_report(self, report_id):
        response = self.client_get(
            f"/api/v1/reports/{report_id}/",
            name="retrieve_report",
            timeout=TIMEOUT,
        )
        if response and response.status_code == 200:
            return response.json()
        raise Exception("Failed to retrieve report")

    def retrieve_report_id_and_coverage_from_date_list(self):
        response = self.client_get(
            "/api/v1/reports/",
            name="retrieve_report_ids_and_coverage_from_dates",
            timeout=TIMEOUT,
        )
        if response and response.status_code == 200:
            retval = {}
            reports = response.json()
            for report in reports:
                retval[report["id"]] = report.get("coverage_from_date", None)
            return retval
        raise Exception("Failed to retrieve report ids/coverage from dates")

    @task
    def celery_test(self):
        self.client_get("/devops/celery-status/", name="celery-status", timeout=TIMEOUT)

    @task
    def load_contacts(self):
        params = {
            "page": 1,
            "ordering": "form_type",
        }
        self.client_get(
            "/api/v1/contacts/", name="load_contacts", timeout=TIMEOUT, params=params
        )

    @task
    def load_reports(self):
        params = {
            "page": 1,
            "ordering": "form_type",
        }
        self.client_get(
            "/api/v1/reports/", name="load_reports", timeout=TIMEOUT, params=params
        )

    @task
    def load_transactions(self):
        if len(self.report_ids) > 0:
            report_id = random.choice(self.report_ids)
            schedules = random.choice(SCHEDULES)
            print(f"\n\n\nREPORT ID: {report_id}\n{self.report_ids}\n\n\n")
            params = {
                "page": 1,
                "ordering": "form_type",
                "schedules": schedules,
                "report_id": report_id,
            }
            self.client_get(
                "/api/v1/transactions/",
                name="load_transactions",
                timeout=TIMEOUT,
                params=params,
            )

    @task
    def submit_reports(self):
        with self.report_ids_to_submit_lock:
            if len(self.report_ids_to_submit) == 0:
                logging.info("No more reports to submit")
                return
            report_id = self.report_ids_to_submit.pop()
        # poll_seconds Determined by INITIAL_POLLING_INTERVAL setting
        self.submit_report(report_id, poll_seconds=40)

    def client_get(self, *args, **kwargs):
        kwargs["catch_response"] = True
        with self.client.get(*args, **kwargs) as response:
            if response.status_code != 200:
                response.failure(f"Non-200 Response: {response.status_code}")
            return response


class Swarm(user.HttpUser):
    tasks = [Tasks]
    wait_time = between(1.5, 4)
