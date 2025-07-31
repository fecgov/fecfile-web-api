import os
import logging
import json
import time
import random
import threading

from locust import between, task, TaskSet, user

# seconds
TIMEOUT = 30  # seconds

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
        self.login()
        self.get_and_activate_commmittee()

        # logging.info("Preparing reports for submit")
        self.report_ids = self.retrieve_report_id_list()
        # self.prepare_reports_for_submit(self.report_ids)
        # self.report_ids_to_submit = self.report_ids.copy()

    def login(self):
        authenticate_response = self.client.get(
            "/api/v1/oidc/authenticate", name="oidc_authenticate", allow_redirects=False
        )
        authenticate_redirect_uri = self.get_redirect_uri(authenticate_response)
        authorize_response = self.client.get(
            authenticate_redirect_uri,
            name="oidc_provider_authorize",
            allow_redirects=False,
        )
        authorize_redirect_uri = self.get_redirect_uri(authorize_response)
        self.client.get(
            authorize_redirect_uri, name="oidc_callback", allow_redirects=False
        )
        self.client.headers["x-csrftoken"] = self.client.cookies["csrftoken"]
        self.client.headers["user-agent"] = "Locust testing"
        self.client.headers["Origin"] = self.client.base_url

    def get_and_activate_commmittee(self):
        committee_id_list = self.retrieve_committee_id_list()
        committee_id = committee_id_list[self.user.user_index]
        response = self.client.post(
            f"/api/v1/committees/{committee_id}/activate/",
            name=f"activate_committee_{committee_id}",
        )
        logging.info(response.json())
        if response.status_code != 200:
            raise Exception(
                f"Failed to activate committee for user_index {self.user.user_index}"
            )

    def get_redirect_uri(self, response):
        if response.status_code == 302:
            return response.headers["Location"].removeprefix("http://localhost:8080")
        return None

    # def prepare_reports_for_submit(self, report_ids):
    #     logging.info("Calculating summaries for reports")
    #     report_json_list = self.calculate_summary_for_report_id_list(report_ids)
    #     logging.info("Confirming information for reports")
    #     return self.confirm_information_for_report_json_list(report_json_list)

    # def calculate_summary_for_report_id_list(self, report_id_list):
    #     retval = []
    #     for report_id in report_id_list:
    #         try:
    #             retval.append(self.calculate_summary_for_report_id(report_id))
    #         except Exception as e:
    #             print(f"Error calculating summary for report_id {report_id}: {e}")
    #     return retval

    # def calculate_summary_for_report_id(self, report_id, poll_seconds=2):
    #     response = self.client.post(
    #         "/api/v1/web-services/summary/calculate-summary/",
    #         name="calculate_report_summary",
    #         json={"report_id": report_id},
    #     )
    #     if response.status_code != 200:
    #         raise Exception("Failed to create calculate-summary task")
    #     for i in range(3):
    #         time.sleep(poll_seconds)
    #         report_json = self.retrieve_report(report_id)
    #         if report_json.get("calculation_status", None) == "SUCCEEDED":
    #             return report_json
    #     raise Exception("Failed to receive successful summary calculation status")

    # def confirm_information_for_report_json_list(self, report_json_list):
    #     retval = []
    #     for report_json in report_json_list:
    #         try:
    #             retval.append(self.confirm_information_for_report_json(report_json))
    #         except Exception as e:
    #             print(f"Failed to confirm report information for {report_json}: {e}")
    #     return retval

    # def confirm_information_for_report_json(self, report_json):
    #     fields_to_validate = [
    #         "confirmation_email_1",
    #         "confirmation_email_2",
    #         "change_of_address",
    #         "street_1",
    #         "street_2",
    #         "city",
    #         "state",
    #         "zip",
    #     ]
    #     params = {"fields_to_validate": fields_to_validate}
    #     report_id = report_json.get("id", None)
    #     if not report_id:
    #         raise Exception("Report JSON does not contain an id")
    #     report_json["confirmation_email_1"] = "test@test.com"
    #     report_json["hasChangeOfAddress"] = False
    #     response = self.client.put(
    #         f"/api/v1/reports/form-3x/{report_id}/",
    #         name="confirm_report_info_for_submit",
    #         params=params,
    #         json=report_json,
    #     )
    #     if response.status_code != 200:
    #         raise Exception("Failed to update/confirm report information")
    #     return self.retrieve_report(report_id)

    # def submit_report(self, report_id, poll_seconds):
    #     self.update_report_for_submit(report_id)
    #     logging.info(f"================ SUBMITTING FOR: {report_id} ================")
    #     self.submit_to_fec_and_poll_for_success(report_id, poll_seconds)

    # def update_report_for_submit(self, report_id):
    #     fields_to_validate = [
    #         "treasurer_first_name",
    #         "treasurer_last_name",
    #         "treasurer_middle_name",
    #         "treasurer_prefix",
    #         "treasurer_suffix",
    #         "filingPassword",
    #         "userCertified",
    #     ]
    #     params = {"fields_to_validate": fields_to_validate}
    #     report_json = self.retrieve_report(report_id)
    #     report_json["treasurer_last_name"] = "test_treasurer_last_name"
    #     report_json["treasurer_first_name"] = "test_treasurer_first_name"
    #     response = self.client.put(
    #         f"/api/v1/reports/form-3x/{report_id}/",
    #         name="update_report_treasurer_for_submit",
    #         params=params,
    #         json=report_json,
    #     )
    #     if response.status_code != 200:
    #         raise Exception("Failed to update report information for submit")

    # def submit_to_fec_and_poll_for_success(self, report_id, poll_seconds):
    #     with self.client.post(
    #         "/api/v1/web-services/submit-to-fec/",
    #         name="submit_report_to_fec",
    #         json={"report_id": report_id, "password": "fake_pd"},
    #         catch_response=True,
    #     ) as response:
    #         if response.status_code != 200:
    #             response.failure("Failed to post submit to fec task")
    #         for i in range(3):
    #             time.sleep(poll_seconds)
    #             report_json = self.retrieve_report(report_id)
    #             upload_submission = report_json.get("upload_submission", None)
    #             if (
    #                 upload_submission
    #                 and upload_submission.get("fec_status", None) == "ACCEPTED"
    #             ):
    #                 return report_json
    #         response.failure(
    #             f"Failed to get successful fec submit status for report_id {report_id}"
    #         )

    # def retrieve_report(self, report_id):
    #     response = self.client_get(
    #         f"/api/v1/reports/{report_id}/",
    #         name="retrieve_report",
    #         timeout=TIMEOUT,
    #     )
    #     if response and response.status_code == 200:
    #         return response.json()
    #     raise Exception("Failed to retrieve report")

    def retrieve_report_id_list(self):
        response = self.client_get(
            "/api/v1/reports/",
            timeout=TIMEOUT,
        )
        if response and response.status_code == 200:
            retval = []
            reports = response.json()
            for report in reports:
                retval.append(report["id"])
            retval.sort()
            return retval
        raise Exception("Failed to retrieve report ids for load test setup")

    def retrieve_committee_id_list(self):
        response = self.client_get(
            "/api/v1/committees/",
            timeout=TIMEOUT,
        )
        if response and response.status_code == 200:
            retval = []
            committees = response.json()["results"]
            logging.info(f"committees: {committees}")
            committees.sort(key=lambda x: x["committee_id"])
            for committee in committees:
                retval.append(committee["id"])
            return retval
        raise Exception("Failed to retrieve committee ids for load test setup")

    @task
    def user_test(self):
        self.client_get(
            "/api/v1/users/get_current/", name="current_user", timeout=TIMEOUT
        )

    # @task
    # def submit_reports(self):
    #     if len(self.report_ids_to_submit) == 0:
    #         logging.info("No more reports to submit")
    #         return
    #     report_id = self.report_ids_to_submit.pop()
    #     # poll_seconds Determined by INITIAL_POLLING_INTERVAL setting
    #     self.submit_report(report_id, poll_seconds=40)

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

    def client_get(self, *args, **kwargs):
        kwargs["catch_response"] = True
        with self.client.get(*args, **kwargs) as response:
            if response.status_code != 200:
                response.failure(f"Non-200 Response: {response.status_code}")
            logging.info(response.json())
            return response


class Swarm(user.HttpUser):
    def on_start(self):
        self.user_index = user_index_counter.get_and_increment()
        logging.info(f"User index: {self.user_index}")

    tasks = [Tasks]
    wait_time = between(1.5, 4)
