import structlog
import math
from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.user.models import User

from .locust_data_generator import LocustDataGenerator

logger = structlog.get_logger(__name__)

TEST_USER_EMAIL = "test@test.com"


class LoadTestUtils:
    def create_load_test_committees_and_data(
        self,
        base_committee_number,
        number_of_committees,
        number_of_reports,
        number_of_contacts,
        number_of_transactions,
        number_of_receipts,
        number_of_disbursements,
        number_of_loans,
        number_of_debts,
        single_to_tiered_transaction_ratio,
        repayments_per_debt,
    ):
        test_user = User.objects.filter(email__iexact=TEST_USER_EMAIL).first()
        if not test_user:
            logger.info(f"Creating test user: {TEST_USER_EMAIL}")
            User.objects.create(email=TEST_USER_EMAIL, username=TEST_USER_EMAIL)
        logger.info(f"Test user already exists: {TEST_USER_EMAIL}")
        for i in range(number_of_committees):
            new_committee_id = f"C{base_committee_number + i}"
            self.create_load_test_committee_and_data(
                new_committee_id,
                number_of_reports,
                number_of_contacts,
                number_of_transactions,
                number_of_receipts,
                number_of_disbursements,
                number_of_loans,
                number_of_debts,
                single_to_tiered_transaction_ratio,
                repayments_per_debt
            )

    def create_load_test_committee_and_data(
        self,
        new_committee_id,
        number_of_reports,
        number_of_contacts,
        number_of_transactions,
        number_of_receipts,
        number_of_disbursements,
        number_of_loans,
        number_of_debts,
        single_to_tiered_transaction_ratio,
        repayments_per_debt
    ):
        logger.info(f"Creating and activating new committee: {new_committee_id}")
        committee = self.create_new_committee(new_committee_id)
        self.locust_data_generator = LocustDataGenerator(committee)

        # Reports
        logger.info(f"Creating {number_of_reports} reports")
        reports = self.locust_data_generator.generate_form_3x(number_of_reports)

        # Contacts
        logger.info(f"Creating {number_of_contacts} contacts")
        contacts = self.locust_data_generator.generate_contacts(number_of_contacts)

        # Schedule A Transactions
        schedule_a_transactions_needed = math.ceil(
            number_of_receipts or (number_of_transactions/2)
        )
        logger.info(f"Creating {schedule_a_transactions_needed} Sch A transactions")
        self.locust_data_generator.generate_single_schedule_a_transactions(
            math.ceil(schedule_a_transactions_needed * single_to_tiered_transaction_ratio),
            reports,
            contacts,
        )
        self.locust_data_generator.generate_tiered_schedule_a_transactions(
            math.ceil(schedule_a_transactions_needed * (1 - single_to_tiered_transaction_ratio)),
            reports,
            contacts,
        )

        # Schedule B Transactions
        schedule_b_transactions_needed = math.ceil(
            number_of_disbursements or (number_of_transactions/2)
        )
        logger.info(f"Creating {schedule_b_transactions_needed} Sch B transactions")
        self.locust_data_generator.generate_single_schedule_b_transactions(
            math.ceil(schedule_b_transactions_needed * single_to_tiered_transaction_ratio),
            reports,
            contacts,
        )
        self.locust_data_generator.generate_tiered_schedule_b_transactions(
            math.ceil(schedule_b_transactions_needed * (1 - single_to_tiered_transaction_ratio)),
            reports,
            contacts,
        )

        # Schedule C Transactions
        logger.info(f"Creating {number_of_loans} loans")
        self.locust_data_generator.generate_loan_transactions(
            number_of_loans,
            reports,
            contacts
        )

        # Schedule D Transactions
        logger.info(f"Creating {number_of_debts} debts with {repayments_per_debt} repayments each")  # NOQA: E501
        self.locust_data_generator.generate_debt_transactions(
            number_of_debts,
            repayments_per_debt,
            reports,
            contacts,
        )

    def create_new_committee(self, new_committee_id):
        user = User.objects.filter(email__iexact=TEST_USER_EMAIL).first()
        committee = CommitteeAccount.objects.create(committee_id=new_committee_id)
        Membership.objects.create(
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            committee_account_id=committee.id,
            user=user,
        )
        return committee
