import structlog
import math
from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.user.models import User
from django.core.management import call_command

from .locust_data_generator import LocustDataGenerator

logger = structlog.get_logger(__name__)

TEST_USER_EMAIL = "test@test.com"
BACKUP_TEST_USER_EMAIL = "test2@test.com"


class LoadTestUtils:

    def create_load_test_committees_and_data(
        self,
        base_committee_number,
        number_of_committees,
        number_of_reports,
        number_of_contacts,
        number_of_transactions,
        single_to_triple_transaction_ratio,
    ):
        self.create_test_users()
        for i in range(number_of_committees):
            new_committee_id = f"C{base_committee_number + i}"
            self.create_load_test_committee_and_data(
                new_committee_id,
                number_of_reports,
                number_of_contacts,
                number_of_transactions,
                single_to_triple_transaction_ratio,
            )

    def create_load_test_committee_and_data(
        self,
        new_committee_id,
        number_of_reports,
        number_of_contacts,
        number_of_transactions,
        single_to_triple_transaction_ratio,
    ):
        logger.info(f"Creating and activating new committee: {new_committee_id}")
        committee = self.create_new_committee(new_committee_id)
        self.locust_data_generator = LocustDataGenerator(committee)

        logger.info(f"Creating {number_of_reports} reports")
        reports = self.locust_data_generator.generate_form_3x(number_of_reports)

        logger.info(f"Creating {number_of_contacts} contacts")
        contacts = self.locust_data_generator.generate_contacts(number_of_contacts)

        single_transactions_needed = math.ceil(
            number_of_transactions * single_to_triple_transaction_ratio
        )
        logger.info(f"Creating {single_transactions_needed} Sch A single transactions")
        self.locust_data_generator.generate_single_schedule_a_transactions(
            single_transactions_needed,
            reports,
            contacts,
        )
        logger.info(f"Creating {single_transactions_needed} Sch B single transactions")
        self.locust_data_generator.generate_single_schedule_b_transactions(
            single_transactions_needed,
            reports,
            contacts,
        )

        triple_transactions_needed = math.ceil(
            number_of_transactions * (1 - single_to_triple_transaction_ratio)
        )
        logger.info(f"Creating {triple_transactions_needed} Sch A triple transactions")
        self.locust_data_generator.generate_triple_schedule_a_transactions(
            triple_transactions_needed,
            reports,
            contacts,
        )
        logger.info(f"Creating {triple_transactions_needed} Sch B triple transactions")
        self.locust_data_generator.generate_triple_schedule_b_transactions(
            triple_transactions_needed,
            reports,
            contacts,
        )

    def create_new_committee(self, new_committee_id):
        committee = CommitteeAccount.objects.create(committee_id=new_committee_id)
        for email in (TEST_USER_EMAIL, BACKUP_TEST_USER_EMAIL):
            test_user = User.objects.filter(email__iexact=email).first()
            Membership.objects.create(
                role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
                committee_account_id=committee.id,
                user=test_user,
            )
        return committee

    def delete_load_test_committees_and_data(
        self,
        base_committee_number,
        number_of_committees,
    ):
        test_user = User.objects.filter(email__iexact=TEST_USER_EMAIL).first()
        if not test_user:
            logger.error(f"User with email does not exist: {TEST_USER_EMAIL}")
            return
        backup_test_user = User.objects.filter(email__iexact=BACKUP_TEST_USER_EMAIL).first()
        for i in range(number_of_committees):
            committee_id = f"C{base_committee_number + i}"
            committee = CommitteeAccount.objects.filter(committee_id=committee_id).first()
            user_count = Membership.objects.filter(
                role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
                committee_account_id=committee.id
            ).count()
            test_user_membership = Membership.objects.filter(
                role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
                committee_account_id=committee.id,
                user=[test_user,backup_test_user]
            ).count()
            backup_test_user_membership = Membership.objects.filter(
                role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
                committee_account_id=committee.id,
                user=backup_test_user,
            ).first()
            # Make sure test users are the only users
            if user_count <= 2 and test_user_membership and backup_test_user_membership:
                logger.info(f"Deleting committee: {committee_id}")
                call_command("delete_committee_account", committee_id)
            logger.info(f"Skipped deleting committee: {committee_id}")
        self.delete_test_users()

    def create_test_users(self):
        for email in (TEST_USER_EMAIL, BACKUP_TEST_USER_EMAIL):
            test_user = User.objects.filter(email__iexact=email).first()
            if not test_user:
                logger.info(f"Creating test user: {email}")
                User.objects.create(email=email, username=email)
            else:
                logger.info(f"Test user already exists: {email}")


    def delete_test_users(self):
        test_user = User.objects.filter(email__iexact=TEST_USER_EMAIL).first()
        if not test_user:
            logger.error(f"User with email does not exist: {TEST_USER_EMAIL}")
            return
        backup_test_user = User.objects.filter(email__iexact=BACKUP_TEST_USER_EMAIL).first()
        test_user_membership = Membership.objects.filter(
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            user=test_user,
        ).first()
        backup_test_user_membership = Membership.objects.filter(
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            user=backup_test_user,
        ).first()
        try:
            logger.info(f"Deleting test user: {TEST_USER_EMAIL}")
            test_user.delete()
            logger.info(f"Deleted test user successfully: {TEST_USER_EMAIL}")
            logger.info(f"Deleting test user: {BACKUP_TEST_USER_EMAIL}")
            backup_test_user.delete()
            logger.info(f"Deleted test user successfully: {BACKUP_TEST_USER_EMAIL}")
        except Exception as e:
            logger.error(f"An error occurred: {e}")
