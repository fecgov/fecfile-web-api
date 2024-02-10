"""Load testing for the FECFile API and web app. Run from command directory using the

`docker-compose --profile locust up -d`

Go to http://0.0.0.0:8089/ to run tests.

Recommended tests:
100 users / 1 ramp-up rate
500 users / 5 ramp-up rate

*Run on other spaces:*
Log in to that environment, and get the session ID from the header and update the
OIDC_SESSION_ID environment variable on your local machine

Modifying docker-compose:
-f /mnt/locust/locustfile.py --master -H https://fecfile-web-api-dev.app.cloud.gov

Scale up using docker:
docker-compose --profile locust up -d --scale locust-follower=4

Environment variables:
Ask team about what to set for
`LOCAL_TEST_USER` and `LOCAL_TEST_PWD`

Get `OIDC_SESSION_ID` from an authenticated sesion

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
            response = self.client.post(
                "/api/v1/user/login/authenticate",
                json={"username": TEST_USER, "password": TEST_PWD}
            )
            csrftoken = response.cookies.get('csrftoken')
            self.client.headers = {
                "X-CSRFToken": csrftoken
            }
            if len(self.fetch_ids("reports", "id")) < 10:
                logging.info("Not enough reports, creating some")
                self.create_report()
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
            "submitAlertText": "Are you sure you want to submit this form electronically? Please note that you cannot undo this action. Any changes needed will need to be filed as an amended report.",
            "schema": {
                "$schema": "http://json-schema.org/draft-07/schema",
                "$id": "https://github.com/fecgov/fecfile-validate/blob/main/schema/F3X.json",
                "version": "8.3.0.1",
                "title": "FEC F3X",
                "type": "object",
                "required": [
                    "form_type",
                    "filer_committee_id_number",
                    "treasurer_last_name",
                    "treasurer_first_name",
                    "date_signed"
                ],
                "fec_recommended": [
                    "committee_name",
                    "street_1",
                    "city",
                    "state",
                    "zip",
                    "report_code",
                    "election_code",
                    "date_of_election",
                    "state_of_election",
                    "coverage_from_date",
                    "coverage_through_date"
                ],
                "properties": {
                    "form_type": {
                        "enum": [
                            "F3XN",
                            "F3XA",
                            "F3XT"
                        ]
                    },
                    "filer_committee_id_number": {
                        "type": "string",
                        "minLength": 9,
                        "maxLength": 9,
                        "pattern": "^[C|P][0-9]{8}$|^[H|S][0-9]{1}[A-Z]{2}[0-9]{5}$"
                    },
                    "committee_name": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 0,
                        "maxLength": 200,
                        "pattern": "^[ -~]{0,200}$"
                    },
                    "change_of_address": {
                        "type": [
                            "boolean",
                            "null"
                        ]
                    },
                    "street_1": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 0,
                        "maxLength": 34,
                        "pattern": "^[ -~]{0,34}$"
                    },
                    "street_2": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 0,
                        "maxLength": 34,
                        "pattern": "^[ -~]{0,34}$"
                    },
                    "city": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 0,
                        "maxLength": 30,
                        "pattern": "^[ -~]{0,30}$"
                    },
                    "state": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 2,
                        "maxLength": 2,
                        "pattern": "^[A-Z]{2}$"
                    },
                    "zip": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 5,
                        "maxLength": 9,
                        "pattern": "^[ -~]{0,9}$"
                    },
                    "report_code": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 0,
                        "maxLength": 3,
                        "pattern": "^[ -~]{0,3}$"
                    },
                    "election_code": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 0,
                        "maxLength": 5,
                        "pattern": "^[ -~]{0,5}$"
                    },
                    "date_of_election": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 10,
                        "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
                    },
                    "state_of_election": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 2,
                        "maxLength": 2,
                        "pattern": "^[A-Z]{2}$"
                    },
                    "coverage_from_date": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 10,
                        "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
                    },
                    "coverage_through_date": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 10,
                        "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
                    },
                    "qualified_committee": {
                        "type": [
                            "boolean",
                            "null"
                        ]
                    },
                    "treasurer_last_name": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 30,
                        "pattern": "^[ -~]{0,30}$"
                    },
                    "treasurer_first_name": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 20,
                        "pattern": "^[ -~]{0,20}$"
                    },
                    "treasurer_middle_name": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 0,
                        "maxLength": 20,
                        "pattern": "^[ -~]{0,20}$"
                    },
                    "treasurer_prefix": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 0,
                        "maxLength": 10,
                        "pattern": "^[ -~]{0,10}$"
                    },
                    "treasurer_suffix": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 0,
                        "maxLength": 10,
                        "pattern": "^[ -~]{0,10}$"
                    },
                    "date_signed": {
                        "type": "string",
                        "minLength": 10,
                        "pattern": "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
                    },
                    "L6b_cash_on_hand_beginning_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L6c_total_receipts_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L6d_subtotal_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L7_total_disbursements_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L8_cash_on_hand_at_close_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L9_debts_to_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L10_debts_by_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L11ai_itemized_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L11aii_unitemized_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L11aiii_total_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L11b_political_party_committees_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L11c_other_political_committees_pacs_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L11d_total_contributions_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L12_transfers_from_affiliated_other_party_cmtes_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L13_all_loans_received_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L14_loan_repayments_received_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L15_offsets_to_operating_expenditures_refunds_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L16_refunds_of_federal_contributions_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L17_other_federal_receipts_dividends_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L18a_transfers_from_nonfederal_account_h3_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L18b_transfers_from_nonfederal_levin_h5_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L18c_total_nonfederal_transfers_18a_18b_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L19_total_receipts_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L20_total_federal_receipts_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L21ai_federal_share_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L21aii_nonfederal_share_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L21b_other_federal_operating_expenditures_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L21c_total_operating_expenditures_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L22_transfers_to_affiliated_other_party_cmtes_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L23_contributions_to_federal_candidates_cmtes_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L24_independent_expenditures_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L25_coordinated_expend_made_by_party_cmtes_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L26_loan_repayments_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L27_loans_made_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L28a_individuals_persons_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L28b_political_party_committees_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L28c_other_political_committees_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L28d_total_contributions_refunds_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L29_other_disbursements_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L30ai_shared_federal_activity_h6_fed_share_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L30aii_shared_federal_activity_h6_nonfed_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L30b_nonallocable_fed_election_activity_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L30c_total_federal_election_activity_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L31_total_disbursements_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L32_total_federal_disbursements_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L33_total_contributions_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L34_total_contribution_refunds_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L35_net_contributions_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L36_total_federal_operating_expenditures_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L37_offsets_to_operating_expenditures_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L38_net_operating_expenditures_period": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L6a_cash_on_hand_jan_1_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L6a_year_for_above_ytd": {
                        "type": [
                            "string",
                            "null"
                        ],
                        "minLength": 4,
                        "maxLength": 4,
                        "pattern": "^[0-9]{4}$"
                    },
                    "L6c_total_receipts_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L6d_subtotal_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L7_total_disbursements_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L8_cash_on_hand_close_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L11ai_itemized_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L11aii_unitemized_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L11aiii_total_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L11b_political_party_committees_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L11c_other_political_committees_pacs_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L11d_total_contributions_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L12_transfers_from_affiliated_other_party_cmtes_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L13_all_loans_received_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L14_loan_repayments_received_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L15_offsets_to_operating_expenditures_refunds_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L16_refunds_of_federal_contributions_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L17_other_federal_receipts_dividends_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L18a_transfers_from_nonfederal_account_h3_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L18b_transfers_from_nonfederal_levin_h5_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L18c_total_nonfederal_transfers_18a_18b_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L19_total_receipts_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L20_total_federal_receipts_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L21ai_federal_share_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L21aii_nonfederal_share_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L21b_other_federal_operating_expenditures_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L21c_total_operating_expenditures_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L22_transfers_to_affiliated_other_party_cmtes_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L23_contributions_to_federal_candidates_cmtes_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L24_independent_expenditures_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L25_coordinated_expend_made_by_party_cmtes_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L26_loan_repayments_made_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L27_loans_made_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L28a_individuals_persons_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L28b_political_party_committees_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L28c_other_political_committees_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L28d_total_contributions_refunds_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L29_other_disbursements_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L30ai_shared_federal_activity_h6_fed_share_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L30aii_shared_federal_activity_h6_nonfed_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L30b_nonallocable_fed_election_activity_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L30c_total_federal_election_activity_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L31_total_disbursements_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L32_total_federal_disbursements_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L33_total_contributions_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L34_total_contribution_refunds_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L35_net_contributions_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L36_total_federal_operating_expenditures_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L37_offsets_to_operating_expenditures_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    },
                    "L38_net_operating_expenditures_ytd": {
                        "type": [
                            "number",
                            "null"
                        ],
                        "minimum": 0,
                        "maximum": 999999999.99
                    }
                }
            },
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


    @task
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
