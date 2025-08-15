import structlog
import math

from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.contacts.models import Contact
from fecfiler.user.models import User
from .locust_data_generator import LocustDataGenerator

logger = structlog.get_logger(__name__)


class LoadTestUtils:
    def create_load_test_committee_and_data(
        self,
        test_user_email,
        new_committee_id,
        number_of_reports,
        number_of_contacts,
        number_of_transactions,
        single_to_triple_transaction_ratio,
    ):
        logger.info(f"Creating and activating new committee: {new_committee_id}")
        committee = self.create_new_committee(new_committee_id, test_user_email)
        self.locust_data_generator = LocustDataGenerator(committee)

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

    def create_new_committee(self, new_committee_id, test_user_email):
        user = User.objects.filter(email__iexact=test_user_email).first()
        committee = CommitteeAccount.objects.create(committee_id=new_committee_id)
        Membership.objects.create(
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            committee_account_id=committee.id,
            user=user,
        )
        return committee

    def create_reports(self, number_of_reports):
        return self.locust_data_generator.generate_form_3x(number_of_reports)

    def create_contacts(self, number_of_contacts):
        contact_json_list = self.locust_data_generator.generate_contacts(
            number_of_contacts
        )
        return Contact.objects.bulk_create(contact_json_list)

    def create_single_transactions(self, number_of_transactions, reports, contacts):
        self.locust_data_generator.generate_single_transactions(
            number_of_transactions,
            reports,
            contacts,
        )

    def create_triple_transactions(self, number_of_transactions, reports, contacts):
        self.locust_data_generator.generate_triple_transactions(
            number_of_transactions, reports, contacts
        )
