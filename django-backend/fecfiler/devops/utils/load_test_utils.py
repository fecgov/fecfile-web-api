import requests
import structlog
import math

from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.models import Report
from fecfiler.contacts.models import Contacts
from fecfiler.transactions.models import Transactions
from locust_data_generator import LocustDataGenerator

logger = structlog.get_logger(__name__)


class LoadTestUtils:
    def __init__(self, base_uri, session_id, csrf_token):
        self.headers = {
            "cookie": f"sessionid={session_id}; csrftoken={csrf_token};",
            "user-agent": "Locust testing",
            "x-csrftoken": csrf_token,
            "Origin": base_uri,
        }
        self.base_uri = base_uri

    def create_load_test_committee_and_data(
        self,
        new_committee_id="C33333333",
        number_of_reports=10,
        number_of_contacts=100,
        number_of_transactions=500,
        single_to_triple_transaction_ratio=9 / 10,
    ):
        logger.info(f"Creating and activating new committee: {new_committee_id}")
        committee_uuid = self.create_and_activate_committee(new_committee_id)
        self.locust_data_generator = LocustDataGenerator(committee_uuid)

        logger.info(f"Creating {number_of_reports} reports")
        reports = self.create_reports(number_of_reports)

        logger.info(f"Creating {number_of_contacts} contacts")
        contacts = self.create_contacts(number_of_contacts)

        single_transactions_needed = math.ceil(
            number_of_transactions * single_to_triple_transaction_ratio
        )
        logger.info(f"Creating {single_transactions_needed} single transactions")
        self.create_single_transactions(single_transactions_needed, reports, contacts)

        triple_transactions_needed = math.ceil(
            number_of_transactions * (1 - single_to_triple_transaction_ratio)
        )
        logger.info(f"Creating {triple_transactions_needed} triple transactions")
        self.create_triple_transactions(triple_transactions_needed, reports, contacts)

    def create_and_activate_committee(self, new_committee_id):
        committee = CommitteeAccount.objects.create(committee_id=new_committee_id)
        activate_url = f"{self.base_uri}/committees/{committee.id}/activate/"
        response = requests.post(activate_url, headers=self.headers)
        response.raise_for_status()
        return committee.id

    def create_reports(self, number_of_reports):
        report_json_list = self.locust_data_generator.generate_form_3x(number_of_reports)
        return list(Report.objects.bulk_create(report_json_list))

    def create_contacts(self, number_of_contacts):
        contact_json_list = self.locust_data_generator.generate_contacts(
            number_of_contacts
        )
        return list(Contacts.objects.bulk_create(contact_json_list))

    def create_single_transactions(self, number_of_transactions, reports, contacts):
        single_transaction_json_list = (
            self.locust_data_generator.generate_single_transactions(
                number_of_transactions, contacts, reports
            )
        )
        Transactions.objects.bulk_create(single_transaction_json_list)

    def create_triple_transactions(self, number_of_transactions, reports, contacts):
        triple_transaction_json_list = (
            self.locust_data_generator.generate_triple_transactions(
                number_of_transactions, reports, contacts
            )
        )
        Transactions.objects.bulk_create(triple_transaction_json_list)
