import logging
import time
import threading
import random
from urllib.parse import urlparse
import json
import os
from math import ceil
from copy import deepcopy
import string

from locust import between, task, TaskSet, user, events, runners
from locust.exception import StopUser


SCHEDULES = ["A", "B,E,F", "C,D"]

TIMEOUT = os.environ.get("LOCUST_TIMEOUT", 30)
RETRIEVAL_WEIGHT = os.environ.get("LOCUST_RETRIEVAL_WEIGHT", 5)
DATA_ENTRY_WEIGHT = os.environ.get("LOCUST_DATA_ENTRY_WEIGHT", 2)
FILING_WEIGHT = os.environ.get("LOCUST_FILING_WEIGHT", 1)

SCHEDULE_A_MULTIPLIER = 1
SCHEDULE_B_MULTIPLIER = 1
SCHEDULE_C_MULTIPLIER = 1
SCHEDULE_D_MULTIPLIER = 1

# The rate of new contacts created for transactions vs existing contacts
TRANSACTION_NEW_CONTACT_RATE = 1 / 4

UPDATE_TRANSACTION_MULTIPLIER = 0.5
DELETE_TRANSACTION_MULTIPLIER = 0.5

CONTACT_CREATION_MULTIPLIER = 1

SUMMARY_CALCULATION_MULTIPLIER = 3
AMEND_MULTIPLIER = 0.2

# Tracks state of Payload Contacts between test runs
CREATED_PAYLOAD_CONTACTS = False

# Do we want long transaction chains? Accepts "true"/"True"/"1", otherwise false
LONG_CHAINS = str(os.environ.get("LONG_CHAINS", "false")).lower() in ("true", "1")

# Lower the interval between log reports to prevent log queue overflow
runners.WORKER_LOG_REPORT_INTERVAL = 2


class AtomicInteger:
    def __init__(self, initial_value):
        self._initial_value = initial_value
        self._value = initial_value
        self._lock = threading.Lock()

    def get_and_increment(self):
        with self._lock:
            retval = self._value
            self._value += 1
            return retval

    def reset(self):
        with self._lock:
            self._value = self._initial_value
            return True
        logging.error("Failed to reset user index")


user_index_counter = AtomicInteger(0)


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    logging.info("Test run starting")
    logging.info("Reseting user index")

    resetted = user_index_counter.reset()
    reset_attempts = 0
    while not resetted:
        reset_attempts += 1
        logging.error(f"Failed to reset user index counter {reset_attempts} times")
        resetted = user_index_counter.reset()

        if reset_attempts >= 20:
            raise Exception("Failed to reset user index counter")

    logging.info("Successfully reset user index counter")


class Tasks(TaskSet):
    report_ids = []
    contacts = []
    created_contacts = {
        "IND": {},
        "ORG": {},
        "CAN": {},
        "COM": {},
    }
    saved_schedule_a = None
    saved_schedule_b = None
    saved_schedule_c = None

    def on_start(self):
        logging.info("Logging in")
        self.login()

        logging.info("Getting and activating committee")
        self.get_and_activate_commmittee()

        logging.info("Checking for committee administrators")
        self.get_committee_admins()

        logging.info("Loading default page")
        self.get_post_login_page()

        logging.info("Loading payloads")
        self.load_payloads()

        logging.info("Creating one report")
        self.create_one_report()

        # Setup for tests
        logging.info("Creating contacts")
        self.create_payload_contacts()

        logging.info("Retrieving all contacts")
        found_contacts_count = self.retrieve_all_contacts()
        logging.info(f"Found {found_contacts_count} contacts")

        logging.info("Getting report IDs")
        self.get_report_ids()

        time.sleep(5)

    @task(ceil(RETRIEVAL_WEIGHT))
    def get_contacts(self):
        params = {
            "page": 1,
            "ordering": "sort_name",
            "page_size": random.choice([5, 10, 15, 20])
        }
        self.client_get(
            "/api/v1/contacts/", name="get_contacts", timeout=TIMEOUT, params=params
        )

    @task(ceil(RETRIEVAL_WEIGHT))
    def get_reports(self):
        params = {
            "page": 1,
            "ordering": "form_type",
        }
        self.client_get(
            "/api/v1/reports/", name="get_reports", timeout=TIMEOUT, params=params
        )
        self.load_report_page()

    @task(ceil(RETRIEVAL_WEIGHT))
    def lookup_committees(self):
        params = {
            # Querying with only a single character avoids FEC lookups
            "q": random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            "max_fec_results": 10,
            "max_fecfile_results": 5,
            "exclude_fec_ids": None,
            "exclude_ids": None
        }
        self.client_get(
            "/api/v1/contacts/committee_lookup/",
            name="_lookup_committees",
            timeout=TIMEOUT,
            params=params
        )

    @task(ceil(RETRIEVAL_WEIGHT))
    def lookup_candidates(self):
        params = {
            # Querying with only a single character avoids FEC lookups
            "q": random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ"),
            "max_fec_results": 10,
            "max_fecfile_results": 5,
            "exclude_fec_ids": None,
            "exclude_ids": None
        }
        self.client_get(
            "/api/v1/contacts/candidate_lookup/",
            name="_lookup_candidates",
            timeout=TIMEOUT,
            params=params
        )

    @task(ceil(RETRIEVAL_WEIGHT))
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

    @task(ceil(DATA_ENTRY_WEIGHT * SCHEDULE_A_MULTIPLIER))
    def create_schedule_a_transaction(self):
        if len(self.report_ids) == 0:
            return

        contact_data = self.get_contact_of_type("IND")
        transaction_data = deepcopy(self.transaction_payloads["INDIVIDUAL_RECEIPT"])
        report_id = random.choice(self.report_ids)
        contribution_date = self.report_ids_dict[report_id]

        transaction_data["contact_1"] = contact_data
        transaction_data["contact_1_id"] = contact_data.get("id")
        transaction_data["report_ids"].append(report_id)
        transaction_data["contribution_date"] = contribution_date
        transaction_data["contribution_amount"] = random.randrange(25, 10000)

        if contact_data.get("id") is not None:
            self.get_previous_transaction_by_entity(
                contact_data.get("id"),
                contribution_date,
                "GENERAL"
            )

        time.sleep(1)

        response = self.client.post(
            "/api/v1/transactions/",
            name="create_new_schedule_a_transaction",
            json=transaction_data,
        )
        if response.status_code != 200:
            raise Exception("Failed to POST new Schedule A transaction")

        # if LONG_CHAINS is true then we only want to save a "first" transaction,
        # otherwise we always save the current one so we have the last transaction
        if not self.saved_schedule_a or not LONG_CHAINS:
            self.saved_schedule_a = response.json()

    @task(ceil(DATA_ENTRY_WEIGHT * SCHEDULE_B_MULTIPLIER / 2))
    def create_schedule_b_transaction(self):
        if len(self.report_ids) == 0:
            return

        contact_data = self.get_contact_of_type("IND")
        transaction_data = deepcopy(self.transaction_payloads["OPERATING_EXPENDITURE"])
        report_id = random.choice(self.report_ids)
        expenditure_date = self.report_ids_dict[report_id]

        transaction_data["contact_1"] = contact_data
        transaction_data["contact_1_id"] = contact_data.get("id")
        transaction_data["report_ids"].append(report_id)
        transaction_data["expenditure_date"] = expenditure_date
        transaction_data["expenditure_amount"] = random.randrange(25, 10000)

        if contact_data.get("id") is not None:
            self.get_previous_transaction_by_entity(
                contact_data.get("id"),
                expenditure_date,
                "GENERAL_DISBURSEMENT"
            )

        time.sleep(1)

        response = self.client.post(
            "/api/v1/transactions/",
            name="create_new_schedule_b_transaction",
            json=transaction_data,
        )
        if response.status_code != 200:
            raise Exception("Failed to POST new Schedule B transaction")
        if not self.saved_schedule_b or not LONG_CHAINS:
            self.saved_schedule_b = response.json()

    @task(ceil(DATA_ENTRY_WEIGHT * SCHEDULE_B_MULTIPLIER / 2))
    def create_schedule_b_election_transaction(self):
        if len(self.report_ids) == 0:
            return

        contact_data = self.get_contact_of_type("ORG")
        contact_2_data = self.get_contact_of_type("CAN")
        transaction_data = deepcopy(
            self.transaction_payloads["CONTRIBUTION_TO_CANDIDATE"]
        )
        report_id = random.choice(self.report_ids)
        expenditure_date = self.report_ids_dict[report_id]

        transaction_data["contact_1"] = contact_data
        transaction_data["contact_1_id"] = contact_data.get("id")
        transaction_data["contact_2"] = contact_2_data
        transaction_data["contact_2_id"] = contact_2_data.get("id")
        transaction_data["report_ids"].append(report_id)
        transaction_data["expenditure_date"] = expenditure_date
        transaction_data["expenditure_amount"] = random.randrange(25, 10000)

        self.get_previous_transaction_by_election(
            transaction_data["election_code"],
            transaction_data["beneficiary_candidate_office"],
            transaction_data["beneficiary_candidate_state"],
            expenditure_date,
            transaction_data["aggregation_group"]
        )

        time.sleep(1)

        response = self.client.post(
            "/api/v1/transactions/",
            name="create_new_schedule_b_transaction",
            json=transaction_data,
        )
        if response.status_code != 200:
            raise Exception("Failed to POST new Schedule B transaction")
        if not self.saved_schedule_b or not LONG_CHAINS:
            self.saved_schedule_b = response.json()

    @task(ceil(DATA_ENTRY_WEIGHT * SCHEDULE_C_MULTIPLIER))
    def create_schedule_c_transaction(self):
        if len(self.report_ids) == 0:
            return

        contact_data = self.get_contact_of_type("IND")
        transaction_data = deepcopy(
            self.transaction_payloads["LOAN_RECEIVED_FROM_INDIVIDUAL"]
        )
        report_id = random.choice(self.report_ids)
        loan_incurred_date = self.report_ids_dict[report_id]

        transaction_data["contact_1"] = contact_data
        transaction_data["contact_1_id"] = contact_data.get("id")
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
            raise Exception("Failed to POST new Schedule C transaction")
        if not self.saved_schedule_c or not LONG_CHAINS:
            self.saved_schedule_c = response.json()

    @task(ceil(DATA_ENTRY_WEIGHT * SCHEDULE_D_MULTIPLIER))
    def create_schedule_d_transaction(self):
        if len(self.report_ids) == 0:
            return

        contact_data = self.get_contact_of_type("ORG")
        transaction_data = deepcopy(self.transaction_payloads["DEBT_OWED_BY_COMMITTEE"])
        report_id = random.choice(self.report_ids)

        transaction_data["contact_1"] = contact_data
        transaction_data["contact_1_id"] = contact_data.get("id")
        transaction_data["report_ids"].append(report_id)
        transaction_data["incurred_amount"] = random.randrange(100, 10000)
        transaction_data["balance_at_close"] = transaction_data["incurred_amount"]

        response = self.client.post(
            "/api/v1/transactions/",
            name="create_new_schedule_d_transaction",
            json=transaction_data,
        )
        if response.status_code != 200:
            raise Exception("Failed to POST new Schedule D transaction")

    @task(
        ceil(DATA_ENTRY_WEIGHT * SCHEDULE_A_MULTIPLIER * UPDATE_TRANSACTION_MULTIPLIER)
    )
    def update_schedule_a_transaction(self):
        transaction_id = self.saved_schedule_a
        if transaction_id:
            response = self.client_get(
                f"/api/v1/transactions/{transaction_id}/",
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
            else:
                raise Exception(
                    f"Failed to update Schedule A transaction with response: "
                    f"{response.status_code} - {response.text}"
                )
        else:
            raise Exception("No Schedule A transaction to update")

    @task(
        ceil(DATA_ENTRY_WEIGHT * SCHEDULE_A_MULTIPLIER * UPDATE_TRANSACTION_MULTIPLIER)
    )
    def delete_schedule_a_transaction(self):
        if len(self.report_ids) > 0:
            report_id = random.choice(self.report_ids)
            transaction = self.get_first_individual_receipt_for_report(report_id)
            if transaction:
                response = self.client.delete(
                    f"/api/v1/transactions/{transaction["id"]}/",
                    name="delete_schedule_a_transaction",
                )
                if response.status_code == 204:
                    # if we happened to delete our saved pointer, clear it so it gets reset
                    if transaction == self.saved_schedule_a:
                        self.saved_schedule_a = None
                    return
        raise Exception("Failed to DELETE Schedule A transaction")

    @task(
        ceil(DATA_ENTRY_WEIGHT * SCHEDULE_B_MULTIPLIER * UPDATE_TRANSACTION_MULTIPLIER)
    )
    def update_schedule_b_transaction(self):
        transaction_id = self.saved_schedule_b
        if transaction_id:
            response = self.client_get(
                f"/api/v1/transactions/{transaction_id}/",
                name="get_schedule_b_transaction_by_id",
                timeout=TIMEOUT,
            )
            if response and response.status_code == 200:
                data = response.json()
                data["expenditure_amount"] = 1.23
                data["schedule_id"] = "B"
                data["schema_name"] = data.get(
                    "schema_name",
                    self.transaction_payloads["OPERATING_EXPENDITURE"].get(
                        "schema_name", "DISBURSEMENTS"
                    ),
                )
                response = self.client.put(
                    f"/api/v1/transactions/{data["id"]}/",
                    name="update_schedule_b_transaction",
                    json=data,
                )
            if response.status_code == 200:
                return
            else:
                raise Exception(
                    f"Failed to update Schedule B transaction with response: "
                    f"{response.status_code} - {response.text}"
                )
        else:
            raise Exception("No Schedule B transaction to update")

    @task(
        ceil(DATA_ENTRY_WEIGHT * SCHEDULE_C_MULTIPLIER * UPDATE_TRANSACTION_MULTIPLIER)
    )
    def update_schedule_c_transaction(self):
        transaction_id = self.saved_schedule_c
        if transaction_id:
            response = self.client_get(
                f"/api/v1/transactions/{transaction_id}/",
                name="get_schedule_c_transaction_by_id",
                timeout=TIMEOUT,
            )
            if response and response.status_code == 200:
                data = response.json()
                data["loan_amount"] = 123.45
                data["loan_payment_to_date"] = 24.69
                data["loan_balance"] = 98.76
                data["schedule_id"] = "C"
                data["schema_name"] = data.get(
                    "schema_name",
                    self.transaction_payloads["LOAN_RECEIVED_FROM_INDIVIDUAL"].get(
                        "schema_name", "LOANS"
                    ),
                )
                data["fields_to_validate"] = self.transaction_payloads[
                    "LOAN_RECEIVED_FROM_INDIVIDUAL"
                ].get("fields_to_validate", [])

                response = self.client.put(
                    f"/api/v1/transactions/{data["id"]}/",
                    name="update_schedule_c_transaction",
                    json=data,
                )

            if response.status_code == 200:
                return
            else:
                raise Exception(
                    f"Failed to update Schedule C transaction with response: "
                    f"{response.status_code} - {response.text}"
                )
        else:
            raise Exception("No Schedule C transaction to update")

    @task(ceil(FILING_WEIGHT * SUMMARY_CALCULATION_MULTIPLIER))
    def filing_calculate_summary_only(self):
        if len(self.report_ids) == 0:
            return

        self.client.request_name = "recalculate_report_summary"
        report_id = random.choice(self.report_ids)
        self.calculate_summary_for_report_id(report_id, "calculate_summary_for_report_id")

    @task(ceil(FILING_WEIGHT))
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
        self.report_ids_to_amend.append(self.report_ids_to_submit.pop())

    @task(ceil(FILING_WEIGHT * AMEND_MULTIPLIER))
    def prepare_and_amend_report(self):
        if len(self.report_ids_to_amend) == 0:
            if len(self.report_ids_to_submit) == 0:
                logging.info("No more reports to amend")
            else:
                logging.info("No current reports to amend")
            return

        report_id = random.choice(self.report_ids_to_amend)
        logging.info(f"Amending report {report_id}")

        self.amend_report(report_id)
        self.report_ids_to_amend.pop()

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
        self.client.get(authorize_redirect_uri, allow_redirects=False)
        self.client.headers["x-csrftoken"] = self.client.cookies["csrftoken"]
        self.client.headers["user-agent"] = "Locust testing"
        self.client.headers["Origin"] = self.client.base_url

    def get_and_activate_commmittee(self):
        committee_id_list = self.retrieve_committee_id_list()
        if self.user.user_index >= len(committee_id_list):
            logging.info(f"User index: {self.user.user_index} stopping!")
            logging.info("Not enough committees - need 1 per user!")
            raise StopUser()
        # Check if we have enough committees - 1 per user
        # This is going to run once per user (inefficient but so is all of it)
        committee_id = committee_id_list[self.user.user_index]
        response = self.client.post(
            f"/api/v1/committees/{committee_id}/activate/",
            name="_activate_committee",
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed to activate committee for user_index {self.user.user_index}"
            )

    def retrieve_all_contacts(self):
        page = 1
        page_size = 20
        found_contacts = []

        params = {
            "page": page,
            "ordering": "sort_name",
            "page_size": page_size
        }
        response = self.client_get(
            "/api/v1/contacts/", name="get_contacts", timeout=TIMEOUT, params=params
        )

        if response.status_code != 200:
            raise Exception(
                f"Failed to retrieve contact data for user_index {self.user.user_index}"
            )

        data = response.json()
        if data["count"] > 0:
            found_contacts += data["results"]

        while response.status_code == 200:
            page += 1
            params["page"] = page
            response = self.client_get(
                "/api/v1/contacts/", name="get_contacts", timeout=TIMEOUT, params=params
            )

            if response.status_code == 200:
                data = response.json()
                found_contacts += data["results"]

            if data["next"] is None:
                break

        for contact in found_contacts:
            self.created_contacts[contact["type"]][contact["id"]] = deepcopy(contact)

        return len(found_contacts)

    def get_contact_of_type(self, type):
        if random.random() < TRANSACTION_NEW_CONTACT_RATE:
            return self.get_random_contact_data(type)
        else:
            return self.get_created_contact(type)

    def get_random_contact_data(self, type=None):
        if type is None:
            type = random.choice(["IND", "ORG", "CAN", "COM"])

        contact_data = {}
        match(type):
            case "IND":
                contact_data = deepcopy(self.contact_payloads["INDIVIDUAL_CONTACT_1"])
                contact_data["last_name"] = ''.join(
                    random.choices(string.ascii_letters, k=10)
                )
                contact_data["first_name"] = ''.join(
                    random.choices(string.ascii_letters, k=10)
                )
            case "ORG":
                contact_data = deepcopy(self.contact_payloads["ORGANIZATION_CONTACT_1"])
                contact_data["name"] = ''.join(random.choices(string.ascii_letters, k=20))
            case "COM":
                contact_data = deepcopy(self.contact_payloads["COMMITTEE_CONTACT_1"])
                contact_data[
                    "committee_id"
                ] = "C" + "".join(random.choices(string.digits, k=8))
                contact_data["name"] = ''.join(random.choices(string.ascii_letters, k=20))
            case "CAN":
                contact_data = deepcopy(self.contact_payloads["CANDIDATE_CONTACT_1"])
                contact_data["last_name"] = ''.join(
                    random.choices(string.ascii_letters, k=10)
                )
                contact_data["first_name"] = ''.join(
                    random.choices(string.ascii_letters, k=10)
                )
                state = random.choice(["AK", "IL", "MA", "TX", "PN", "IN", "OH", "MO"])
                contact_data[
                    "candidate_id"
                ] = f"S{random.randint(1, 2)}{state}{random.choices(string.digits, k=5)}"
                contact_data["candidate_state"] = state

        contact_data.pop("id")
        return contact_data

    @task(ceil(DATA_ENTRY_WEIGHT * CONTACT_CREATION_MULTIPLIER))
    def create_new_contact(self, type=None):
        contact_data = self.get_random_contact_data(type)

        response = self.client.post(
            "/api/v1/contacts/",
            name="create_new_random_contact",
            json=contact_data,
        )
        if response.status_code != 201:
            raise Exception("Failed to POST new contact")

        created_contact = response.json()
        self.created_contacts[type][created_contact["id"]] = created_contact
        return created_contact

    def get_created_contact(self, type):
        of_type = list(self.created_contacts[type].values())
        if len(of_type) > 0:
            return deepcopy(random.choice(of_type))
        else:
            logging.error(f"No contact of type {type} available!")
            return None

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
        global CREATED_PAYLOAD_CONTACTS
        if CREATED_PAYLOAD_CONTACTS:
            return

        for key in self.contact_payloads:
            data = deepcopy(self.contact_payloads[key])
            response = self.client.post(
                "/api/v1/contacts/",
                name="_create_new_contact",
                json=data,
            )
            if response.status_code != 201:
                raise Exception("Failed to POST new contact")
            created_contact = response.json()
            self.contact_payloads[key]["id"] = created_contact["id"]
            time.sleep(1)

        CREATED_PAYLOAD_CONTACTS = True

    def get_report_ids(self):
        self.report_ids_dict = self.retrieve_report_ids_dict()
        self.report_ids = list(self.report_ids_dict.keys())
        self.report_ids_to_submit = self.report_ids.copy()
        self.report_ids_to_amend = list()

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

    def amend_report(self, report_id):
        response = self.client.post(
            f"/api/v1/reports/{report_id}/amend/",
            name="amend_report",
            json={},
        )
        if response.status_code != 200:
            raise Exception(f"Failed to POST ammendment to report with id {report_id}")

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
            name="retrieve_report",
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

    def get_previous_transaction_by_entity(self, contact_id, date, aggregation_group):
        params = {
            "contact_1_id": contact_id,
            "aggregation_group": aggregation_group,
            "date": date,
        }
        self.client_get(
            "/api/v1/transactions/previous/entity",
            name="get_previous_transaction_by_entity",
            timeout=TIMEOUT,
            params=params,
        )

    def get_previous_transaction_by_election(
        self, election_code, office, state, date, aggregation_group
    ):
        params = {
            "date": date,
            "aggregation_group": aggregation_group,
            "election_code": election_code,
            "office": office,
            "state": state
        }
        self.client_get(
            "/api/v1/transactions/previous/election",
            name="get_previous_transaction_by_election",
            timeout=TIMEOUT,
            params=params,
        )

    def get_committee_admins(self):
        test_name = "check_admins"
        response = self.client.get(
            "/api/v1/users/get_current/",
            name=f"_{test_name}",
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed {test_name} for user_index {self.user.user_index}"
            )
        response = self.client.get(
            "/api/v1/committee-members/",
            name=f"_{test_name}",
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed {test_name} for user_index {self.user.user_index}"
            )

    def get_post_login_page(self):
        self.load_report_page()

    def load_report_page(self):
        params = {
            "page": 1,
            "ordering": "report_code_label",
            "page_size": 5
        }
        # Two calls are made to F24 under the current setup of the reports page
        for form in ("3x", "24", "24", "1m", "99"):
            response = self.client_get(
                f"/api/v1/reports/form-{form}/",
                name="_get_post_login_page",
                timeout=TIMEOUT,
                params=params
            )
            if response.status_code != 200:
                raise Exception(
                    f"Failed to load initial page for user_index {self.user.user_index}"
                )

    def create_one_report(self):
        test_name = "create_one_report"
        response = self.client.get(
            "/api/v1/reports/form-3x/report_code_map/",
            name=f"_{test_name}",
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed {test_name} for user_index {self.user.user_index}"
            )
        response = self.client.get(
            "/api/v1/reports/form-3x/coverage_dates/",
            name=f"_{test_name}",
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed {test_name} for user_index {self.user.user_index}"
            )
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
        # TODO: Why do we do this? list of fields_to_validate
        params = {
            "fields_to_validate": fields_to_validate
        }
        # TODO: From locust data generator - make a function?
        reports_and_dates = [
            ["Q1", "01-01", "03-31"],
            ["Q2", "04-01", "06-30"],
            ["Q3", "07-01", "09-30"],
            ["YE", "10-01", "12-31"],
        ]
        _, from_date, through_date = random.choice(reports_and_dates)
        year = random.randrange(1000, 9999)

        json = {
            "hasChangeOfAddress": "true",
            "can_delete": "false",
            "can_unamend": "false",
            "report_type": "F3X",
            "form_type": "F3XN",
            "report_code": "Q1",
            "date_of_election": None,
            "state_of_election": None,
            "coverage_from_date": f"{year}-{from_date}",
            "coverage_through_date": f"{year}-{through_date}",
            "filing_frequency": "Q",
            "report_type_category": "Election Year"
        }
        response = self.client.post(
            "/api/v1/reports/form-3x/",
            name=f"_{test_name}",
            params=params,
            json=json
        )
        # TODO: Why are some of these 200s and some 201s?
        if response.status_code != 201:
            raise Exception(
                f"Failed {test_name} for user_index {self.user.user_index}"
            )
        report_id = response.json()["id"]
        response = self.client.get(
            f"/api/v1/reports/{report_id}/",
            name=f"_{test_name}",
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed {test_name} for user_index {self.user.user_index}"
            )
        params = {
            "page": 1,
            "ordering": "line_label,created",
            "report_id": report_id,
            "page_size": 5,
        }
        for _ in SCHEDULES:
            response = self.client_get(
                "/api/v1/transactions/",
                name=f"_{test_name}",
                timeout=TIMEOUT,
                params=params,
            )
            if response.status_code != 200:
                raise Exception(
                    f"Failed {test_name} for user_index {self.user.user_index}"
                )

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
