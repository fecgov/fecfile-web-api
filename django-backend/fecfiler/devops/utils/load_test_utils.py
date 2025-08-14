import structlog
import math
from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.user.models import User

from .locust_data_generator import LocustDataGenerator

logger = structlog.get_logger(__name__)


class LoadTestUtils:
    def create_load_test_committees_and_data(
        self,
        test_user_email,
        number_of_committees,
        number_of_reports,
        number_of_contacts,
        number_of_transactions,
        single_to_triple_transaction_ratio,
    ):
        base_committee_number = 33333333
        for i in range(number_of_committees):
            new_committee_id = f"C{base_committee_number + i}"
            self.create_load_test_committee_and_data(
                test_user_email,
                new_committee_id,
                number_of_reports,
                number_of_contacts,
                number_of_transactions,
                single_to_triple_transaction_ratio,
            )

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
        reports = self.locust_data_generator.generate_form_3x(number_of_reports)

        logger.info(f"Creating {number_of_contacts} contacts")
        contacts = self.locust_data_generator.generate_contacts(number_of_contacts)

        single_transactions_needed = math.ceil(
            number_of_transactions * single_to_triple_transaction_ratio
        )
        logger.info(f"Creating {single_transactions_needed} single transactions")
        self.locust_data_generator.generate_single_schedule_a_transactions(
            single_transactions_needed,
            reports,
            contacts,
        )

        triple_transactions_needed = math.ceil(
            number_of_transactions * (1 - single_to_triple_transaction_ratio)
        )
        logger.info(f"Creating {triple_transactions_needed} triple transactions")
        self.locust_data_generator.generate_triple_schedule_a_transactions(
            triple_transactions_needed,
            reports,
            contacts,
        )

    def create_new_committee(self, new_committee_id, test_user_email):
        user = User.objects.filter(email__iexact=test_user_email).first()
        committee = CommitteeAccount.objects.create(committee_id=new_committee_id)
        Membership.objects.create(
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            committee_account_id=committee.id,
            user=user,
        )
        return committee
