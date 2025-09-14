import logging
import time
import threading
import random
from urllib.parse import urlparse
import json
import os
from copy import deepcopy

from locust import between, task, TaskSet, user


TIMEOUT = 30  # seconds
SCHEDULES = ["A", "B,E,F", "C,D"]


class AtomicInteger:
    def __init__(self, initial_value=0):
        self._value = initial_value
        self._lock = threading.Lock()

    def get_and_increment(self):
        with self._lock:
            retval = self._value
            self._value += 1
            return retval


user_index_counter = AtomicInteger(0)


class Tasks(TaskSet):
    report_ids = []
    contacts = []

    def on_start(self):
        logging.info("Logging in")
        self.login()

        logging.info("Getting and activating committee")
        self.get_and_activate_commmittee()

        logging.info("Loading payloads")
        self.load_payloads()

        logging.info("Creating contact")
        self.create_payload_contacts()

        logging.info("Getting report IDs")
        self.get_report_ids()

    @task
    def devops_celery_test(self):
        self.client_get("/devops/celery-status/", name="celery-status", timeout=TIMEOUT)

    @task
    def get_contacts(self):
        params = {
            "page": 1,
            "ordering": "form_type",
        }
        self.client_get(
            "/api/v1/contacts/", name="get_contacts", timeout=TIMEOUT, params=params
        )

    @task
    def get_reports(self):
        params = {
            "page": 1,
            "ordering": "form_type",
        }
        self.client_get(
            "/api/v1/reports/", name="get_reports", timeout=TIMEOUT, params=params
        )

    @task
    def get_schedule_transactions(self):
        if len(self.report_ids) > 0:
            report_id = random.choice(self.report_ids)
            print(f"\n\n\nREPORT ID: {report_id}\n{self.report_ids}\n\n\n")
            params = {
                "page": 1,
                "ordering": "form_type",
                "report_id": report_id,
            }
            for schedule in SCHEDULES:
                params["schedules"] = schedule
                self.client_get(
                    "/api/v1/transactions/",
                    name=f"read_schedule_{schedule}_transactions",
                    timeout=TIMEOUT,
                    params=params,
                )

    @task(100)  # This task will be picked 100 times more often than the default
    def create_schedule_a_transaction(self):
        contact_data = deepcopy(self.contact_payloads["INDIVIDUAL_CONTACT_1"])
        transaction_data = deepcopy(self.transaction_payloads["INDIVIDUAL_RECEIPT"])
        report_id = random.choice(self.report_ids)
        contribution_date = self.report_ids_dict[report_id]

        transaction_data["contact_1"] = contact_data
        transaction_data["contact_1_id"] = contact_data["id"]
        transaction_data["report_ids"].append(report_id)
        transaction_data["contribution_date"] = contribution_date
        transaction_data["contribution_amount"] = random.randrange(25, 10000)

        response = self.client.post(
            "/api/v1/transactions/",
            name="create_new_schedule_a_transaction",
            json=transaction_data,
        )
        if response.status_code != 200:
            raise Exception("Failed to POST new schedule a transaction")

    @task(100)  # This task will be picked 100 times more often than the default
    def create_schedule_b_transaction(self):
        contact_data = deepcopy(self.contact_payloads["INDIVIDUAL_CONTACT_2"])
        transaction_data = deepcopy(self.transaction_payloads["OPERATING_EXPENDITURE"])
        report_id = random.choice(self.report_ids)
        expenditure_date = self.report_ids_dict[report_id]

        transaction_data["contact_1"] = contact_data
        transaction_data["contact_1_id"] = contact_data["id"]
        transaction_data["report_ids"].append(report_id)
        transaction_data["expenditure_date"] = expenditure_date
        transaction_data["expenditure_amount"] = random.randrange(25, 10000)

        response = self.client.post(
            "/api/v1/transactions/",
            name="create_new_schedule_b_transaction",
            json=transaction_data,
        )
        if response.status_code != 200:
            raise Exception("Failed to POST new schedule b transaction")

    @task
    def create_schedule_c_transaction(self):
        contact_data = deepcopy(self.contact_payloads["INDIVIDUAL_CONTACT_3"])
        transaction_data = deepcopy(
            self.transaction_payloads["LOAN_RECEIVED_FROM_INDIVIDUAL"]
        )
        report_id = random.choice(self.report_ids)
        loan_incurred_date = self.report_ids_dict[report_id]

        transaction_data["contact_1"] = contact_data
        transaction_data["contact_1_id"] = contact_data["id"]
        transaction_data["report_ids"].append(report_id)
        transaction_data["loan_incurred_date"] = loan_incurred_date
        transaction_data["loan_due_date"] = add_year_to_date_str(loan_incurred_date)
        transaction_data["loan_amount"] = random.randrange(100, 10000)

        child_transaction_data = transaction_data["children"][0]
        child_transaction_data["contact_1"] = contact_data
        child_transaction_data["contact_1_id"] = contact_data["id"]
        child_transaction_data["contribution_date"] = transaction_data["loan_due_date"]
        child_transaction_data["contribution_amount"] = transaction_data["loan_amount"]
        child_transaction_data["contribution_aggregate"] = transaction_data["loan_amount"]

        response = self.client.post(
            "/api/v1/transactions/",
            name="create_new_schedule_c_transaction",
            json=transaction_data,
        )
        if response.status_code != 200:
            raise Exception("Failed to POST new schedule c transaction")

    @task(10)  # This task will be picked 10 times more often than the default
    def create_schedule_d_transaction(self):
        contact_data = deepcopy(self.contact_payloads["ORGANIZATION_CONTACT_1"])
        transaction_data = deepcopy(self.transaction_payloads["DEBT_OWED_BY_COMMITTEE"])
        report_id = random.choice(self.report_ids)

        transaction_data["contact_1"] = contact_data
        transaction_data["contact_1_id"] = contact_data["id"]
        transaction_data["report_ids"].append(report_id)
        transaction_data["incurred_amount"] = random.randrange(100, 10000)
        transaction_data["balance_at_close"] = transaction_data["incurred_amount"]

        response = self.client.post(
            "/api/v1/transactions/",
            name="create_new_schedule_d_transaction",
            json=transaction_data,
        )
        if response.status_code != 200:
            raise Exception("Failed to POST new schedule d transaction")

    @task(100)  # This task will be picked 100 times more often than the default
    def update_schedule_a_transaction(self):
        if len(self.report_ids) > 0:
            report_id = random.choice(self.report_ids)
            transaction = self.get_first_individual_receipt_for_report(report_id)
            if transaction:
                response = self.client_get(
                    f"/api/v1/transactions/{transaction["id"]}/",
                    name="get_schedule_a_transaction_by_id",
                    timeout=TIMEOUT,
                )
                if response and response.status_code == 200:
                    data = response.json()
                    data["contribution_amount"] = 1.23
                    data["schedule_id"] = "A"
                    data["schema_name"] = "INDIVIDUAL_RECEIPT"
                    response = self.client.put(
                        f"/api/v1/transactions/{data["id"]}/",
                        name="update_schedule_a_transaction",
                        json=data,
                    )
                if response.status_code == 200:
                    return
        raise Exception("Failed to PUT update schedule a transaction")

    @task
    def delete_schedule_a_transaction(self):
        if len(self.report_ids) > 0:
            report_id = random.choice(self.report_ids)
            transaction = self.get_first_individual_receipt_for_report(report_id)
            if transaction:
                response = self.client.delete(
                    f"/api/v1/transactions/{transaction['id']}/",
                    name="delete_schedule_a_transaction",
                )
                if response.status_code == 204:
                    return
        raise Exception("Failed to DELETE schedule a transaction")

    @task(100)
    def filing_calculate_summary_only(self):
        self.client.request_name = "recalculate_report_summary"
        report_id = random.choice(self.report_ids)
        self.calculate_summary_for_report_id(
            report_id, "filing_calculate_summary_for_report_id"
        )

    @task(500)
    def filing_prepare_and_submit_report(self):
        if len(self.report_ids_to_submit) == 0:
            logging.info("No more reports to submit")
            return
        report_id = random.choice(self.report_ids_to_submit)
        report_json = self.retrieve_report(report_id)

        self.calculate_summary_for_report_id(
            report_id, "filing_1_calculate_report_summary"
        )
        self.confirm_information_for_report_json(report_json)
        self.submit_report(report_id, poll_seconds=40)
        self.report_ids_to_submit.pop()

    def login(self):
        self.client.request_name = "_log_in"
        authenticate_response = self.client.get(
            "/api/v1/oidc/authenticate", allow_redirects=False
        )
        authenticate_redirect_uri = get_redirect_uri(authenticate_response)
        authorize_response = self.client.get(
            authenticate_redirect_uri,
            allow_redirects=False,
        )
        authorize_redirect_uri = get_redirect_uri(authorize_response)
        self.client.get(
            authorize_redirect_uri, allow_redirects=False
        )
        self.client.headers["x-csrftoken"] = self.client.cookies["csrftoken"]
        self.client.headers["user-agent"] = "Locust testing"
        self.client.headers["Origin"] = self.client.base_url

    def get_and_activate_commmittee(self):
        committee_id_list = self.retrieve_committee_id_list()
        committee_id = committee_id_list[self.user.user_index]
        response = self.client.post(
            f"/api/v1/committees/{committee_id}/activate/",
            name="_activate_committee",
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed to activate committee for user_index {self.user.user_index}"
            )

    def load_payloads(self):
        directory = os.path.dirname(os.path.abspath(__file__))
        self.contact_payloads = json.load(
            open(
                os.path.join(directory, "locust-data", "load_test_contact_payloads.json")
            )
        )
        self.transaction_payloads = json.load(
            open(
                os.path.join(
                    directory, "locust-data", "load_test_transaction_payloads.json"
                )
            )
        )

    def create_payload_contacts(self):
        for key in self.contact_payloads:
            data = deepcopy(self.contact_payloads[key])
            response = self.client.post(
                "/api/v1/contacts/",
                name="_create_new_contact",
                json=data,
            )
            if response.status_code != 201:
                raise Exception("Failed to POST new contact")
            self.contact_payloads[key]["id"] = response.json()["id"]
            time.sleep(1)

    def get_report_ids(self):
        self.report_ids_dict = self.retrieve_report_ids_dict()
        self.report_ids = list(self.report_ids_dict.keys())
        self.report_ids_to_submit = self.report_ids.copy()

    def calculate_summary_for_report_id(self, report_id, name, poll_seconds=2):
        response = self.client.post(
            "/api/v1/web-services/summary/calculate-summary/",
            name=name,
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
            name="filing_2_confirm_report_info_for_submit",
            params=params,
            json=report_json,
        )
        if response.status_code != 200:
            raise Exception("Failed to update/confirm report information")
        return self.retrieve_report(report_id)

    def submit_report(self, report_id, poll_seconds):
        self.update_report_for_submit(report_id)
        logging.info(f"================ SUBMITTING FOR: {report_id} ================")
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
            name="filing_3_update_report_treasurer_for_submit",
            params=params,
            json=report_json,
        )
        if response.status_code != 200:
            raise Exception("Failed to update report information for submit")

    def submit_to_fec_and_poll_for_success(self, report_id, poll_seconds):
        with self.client.post(
            "/api/v1/web-services/submit-to-fec/",
            name="filing_4_submit_report_to_fec",
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
            name="get_report_by_id",
            timeout=TIMEOUT,
        )
        if response and response.status_code == 200:
            return response.json()
        raise Exception("Failed to retrieve report")

    def retrieve_report_ids_dict(self):
        response = self.client_get(
            "/api/v1/reports/",
            name="_get_report_ids",
            timeout=TIMEOUT,
        )
        if response and response.status_code == 200:
            retval = {}
            reports = response.json()
            for report in reports:
                retval[report["id"]] = report["coverage_from_date"]
            return retval
        raise Exception("Failed to retrieve report ids for load test setup")

    def retrieve_committee_id_list(self):
        response = self.client_get(
            "/api/v1/committees/",
            name="_get_committee_list",
            timeout=TIMEOUT,
        )
        if response and response.status_code == 200:
            retval = []
            committees = response.json()["results"]
            committees.sort(key=lambda x: x["committee_id"])
            for committee in committees:
                retval.append(committee["id"])
            return retval
        raise Exception("Failed to retrieve committee ids for load test setup")

    def get_first_individual_receipt_for_report(self, report_id):
        params = {
            "page": 1,
            "ordering": "-created",
            "schedules": "A",
            "report_id": report_id,
        }
        response = self.client_get(
            "/api/v1/transactions/",
            name="get_transactions",
            timeout=TIMEOUT,
            params=params,
        )
        if response and response.status_code == 200:
            results = response.json().get("results", [])
            for transaction in results:
                if transaction["transaction_type_identifier"] == "INDIVIDUAL_RECEIPT":
                    return transaction
        return None

    def client_get(self, *args, **kwargs):
        kwargs["catch_response"] = True
        with self.client.get(*args, **kwargs) as response:
            if response.status_code != 200:
                response.failure(f"Non-200 Response: {response.status_code}")
            return response


class Swarm(user.HttpUser):
    def on_start(self):
        self.user_index = user_index_counter.get_and_increment()

    tasks = [Tasks]
    wait_time = between(3, 30)


# Utils
def get_redirect_uri(response):
    if response.status_code == 302:
        parsed_url = urlparse(response.headers["Location"])
        return f"{parsed_url.path}?{parsed_url.query}"
    return None


def add_year_to_date_str(date_str):
    """Expects date_str in YYYY-MM-DD format"""
    parts = date_str.split("-")
    if len(parts) != 3:
        raise Exception(f"Invalid date string: {date_str}")
    year = int(parts[0]) + 1
    return f"{year}-{parts[1]}-{parts[2]}"
