import os
import logging
import random
import json
import time
import threading
from copy import deepcopy
from urllib.parse import urlparse, parse_qs

from locust import between, task, TaskSet, user

SESSION_ID = os.environ.get("OIDC_SESSION_ID")
CSRF_TOKEN = os.environ.get("CSRF_TOKEN")

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
        # Authenticate
        response = self.client.get(
            "/api/v1/oidc/authenticate",
            allow_redirects=False
        )
        if 300 <= response.status_code < 400 and 'Location' in response.headers:
            logging.info(f"response.headers['Location']: {response.headers['Location']}")
            redirect_url = response.headers['Location']
            print(f"Redirect status code: {response.status_code}")
            print(f"New URL (before following redirect): {redirect_url}")
        else:
            print(f"No redirect detected for url. Status code: {response.status_code}")

        parts = redirect_url.split("?", 1)
        if len(parts) > 1:
            args = parts[1]
        else:
            args = ""
        print(args)

        # Authorize
        authorize_response = self.client.get(
            f"/api/v1/mock_oidc_provider/authorize?{args}",
            allow_redirects=False
        )
        if 300 <= authorize_response.status_code < 400 and 'Location' in authorize_response.headers:
            logging.info(f"response.headers['Location']: {authorize_response.headers['Location']}")
            redirect_url = authorize_response.headers['Location']
            print(f"Redirect status code: {authorize_response.status_code}")
            print(f"New URL (before following redirect): {redirect_url}")
        else:
            print(f"No redirect detected for url. Status code: {authorize_response.status_code}")

        # Get code from redirect URL
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)

        if 'code' in query_params:
            code = query_params['code'][0]
        # if 'state' in query_params:
        #     state = query_params['state'][0]

        # token
        token_payload = {
            "client_assertion": None,
            "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",  # noqa
            "code": code,
            "grant_type": "authorization_code",
        }
        response = self.client.post(
            "/api/v1/mock_oidc_provider/token",
            data=token_payload,
            allow_redirects=False
        )
        if response and response.status_code == 200:
            logging.info(response.json())
            logging.info(dict(response.cookies))

        session_id = response.cookies.get('sessionid')
        csrf_token = response.cookies.get('csrftoken')

        # TODO: Set these
        self.client.headers = {
            "cookie": f"sessionid={session_id}; csrftoken={csrf_token};",
            "user-agent": "Locust testing",
            "x-csrftoken": csrf_token,
            "Origin": self.client.base_url,
        }

    #     logging.info("Preparing reports for submit")
    #     self.report_ids = self.retrieve_report_id_list()
    #     self.report_ids_to_submit = self.get_report_ids_to_submit(
    #         self.user.user_index, self.report_ids
    #     )
    #     self.prepare_reports_for_submit(self.report_ids_to_submit)

    # def get_report_ids_to_submit(self, user_index, all_report_ids):
    #     user_count = self.user.environment.parsed_options.users
    #     total_report_count = len(all_report_ids)
    #     reports_per_user = (
    #         total_report_count // user_count if total_report_count > user_count else 1
    #     )
    #     start_index = user_index * reports_per_user
    #     end_index = start_index + reports_per_user
    #     logging.info(f"================ user index {user_index} ================")
    #     logging.info(f"start index {start_index} end index {end_index}")
    #     if start_index >= total_report_count:
    #         logging.warning(
    #             f"User index {user_index} exceeds report count. No reports to submit."
    #         )
    #         return []
    #     return deepcopy(all_report_ids[start_index:end_index])

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

    # def submit_to_fec_and_poll_for_success(self, report_id, poll_seconds=2):
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

    # def retrieve_report_id_list(self):
    #     response = self.client_get(
    #         "/api/v1/reports/",
    #         timeout=TIMEOUT,
    #     )
    #     if response and response.status_code == 200:
    #         retval = []
    #         reports = response.json()
    #         for report in reports:
    #             retval.append(report["id"])
    #         retval.sort()
    #         return retval
    #     raise Exception("Failed to retrieve report ids for load test setup")

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

    # @task
    # def load_transactions(self):
    #     if len(self.report_ids) > 0:
    #         report_id = random.choice(self.report_ids)
    #         schedules = random.choice(SCHEDULES)
    #         print(f"\n\n\nREPORT ID: {report_id}\n{self.report_ids}\n\n\n")
    #         params = {
    #             "page": 1,
    #             "ordering": "form_type",
    #             "schedules": schedules,
    #             "report_id": report_id,
    #         }
    #         self.client_get(
    #             "/api/v1/transactions/",
    #             name="load_transactions",
    #             timeout=TIMEOUT,
    #             params=params,
    #         )

    # @task
    # def submit_reports(self):
    #     if len(self.report_ids_to_submit) == 0:
    #         logging.info("No more reports to submit")
    #         return
    #     report_id = self.report_ids_to_submit.pop()
    #     # poll_seconds Determined by INITIAL_POLLING_INTERVAL setting
    #     self.submit_report(report_id, poll_seconds=40)

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
    wait_time = between(1.5, 4)
