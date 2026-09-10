import json
import os
import structlog
import math
from django.conf import settings
from django.db.models import Q
from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.user.models import User

from .locust_data_generator import LocustDataGenerator

logger = structlog.get_logger(__name__)

TEST_USER_EMAIL = "test@test.com"
LOAD_PREFIX = "load-"
REQUIRED_LOAD_RDS_SERVICE = "load-fecfile-api-rds"
LOAD_TEST_CONTACT_CITY = "Testville"
LOAD_TEST_CONTACT_EMPLOYER = "Business Inc."
LOAD_TEST_CONTACT_OCCUPATION = "Job"
LOAD_TEST_REPORT_FORM_TYPE = "F3XN"


class LoadTestUtils:
    def validate_load_mirror_runtime(self):
        app_name, service_names = self.get_cloud_foundry_runtime_identity()

        has_load_app_name = app_name.startswith(LOAD_PREFIX)
        has_required_rds = REQUIRED_LOAD_RDS_SERVICE in service_names

        if has_load_app_name and has_required_rds:
            logger.info(
                "Validated load test runtime context",
                app_name=app_name,
                required_service=REQUIRED_LOAD_RDS_SERVICE,
            )
            return

        raise ValueError(
            "delete_locust_load_test_data can only be run on a load testing mirror"
        )

    def get_cloud_foundry_runtime_identity(self):
        app_name = self.get_cloud_foundry_app_name()
        service_names = self.get_cloud_foundry_service_names()

        if not app_name or not service_names:
            raise ValueError(
                "delete_locust_load_test_data can only be run on a load testing mirror"
            )

        return app_name, service_names

    def get_cloud_foundry_app_name(self):
        vcap_application = os.environ.get("VCAP_APPLICATION")
        if vcap_application:
            try:
                vcap_application_json = json.loads(vcap_application)
            except json.JSONDecodeError as error:
                raise ValueError(
                    "Could not parse VCAP_APPLICATION to determine app name"
                ) from error

            app_name = vcap_application_json.get("application_name")
            if app_name:
                return app_name

        return settings.APPLICATION_NAME

    def get_cloud_foundry_service_names(self):
        vcap_services = os.environ.get("VCAP_SERVICES")
        if not vcap_services:
            return set()

        try:
            vcap_services_json = json.loads(vcap_services)
        except json.JSONDecodeError as error:
            raise ValueError(
                "Could not parse VCAP_SERVICES to determine service names"
            ) from error

        service_names = set()
        for service_instances in vcap_services_json.values():
            for service_instance in service_instances:
                service_name = service_instance.get("name")
                if service_name:
                    service_names.add(service_name)

        return service_names

    def delete_load_test_committees_and_data(self):
        committees_to_delete = CommitteeAccount.all_objects.filter(
            Q(membership__user__email__iexact=TEST_USER_EMAIL)
            | Q(
                contact__city=LOAD_TEST_CONTACT_CITY,
                contact__employer=LOAD_TEST_CONTACT_EMPLOYER,
                contact__occupation=LOAD_TEST_CONTACT_OCCUPATION,
            )
            | Q(report__form_type=LOAD_TEST_REPORT_FORM_TYPE)
        ).distinct()

        committee_ids = list(committees_to_delete.values_list("committee_id", flat=True))
        logger.info(
            "Deleting load test committees",
            committee_count=len(committee_ids),
            committee_ids=committee_ids,
        )

        for committee in committees_to_delete:
            committee.hard_delete()

        self.delete_orphaned_test_user()

    def delete_orphaned_test_user(self):
        test_user = User.objects.filter(email__iexact=TEST_USER_EMAIL).first()
        if not test_user:
            return

        has_memberships = Membership.objects.filter(user=test_user).exists()
        if has_memberships:
            logger.info(
                "Skipping test user delete due to remaining memberships",
                user_email=TEST_USER_EMAIL,
            )
            return

        test_user.delete()
        logger.info("Deleted load test user", user_email=TEST_USER_EMAIL)

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
            number_of_receipts or (number_of_transactions / 2)
        )
        logger.info(f"Creating {schedule_a_transactions_needed} Sch A transactions")
        self.locust_data_generator.generate_single_schedule_a_transactions(
            math.ceil(
                schedule_a_transactions_needed
                * single_to_tiered_transaction_ratio
            ),
            reports,
            contacts,
        )
        self.locust_data_generator.generate_tiered_schedule_a_transactions(
            math.ceil(
                schedule_a_transactions_needed
                * (1 - single_to_tiered_transaction_ratio)
            ),
            reports,
            contacts,
        )

        # Schedule B Transactions
        schedule_b_transactions_needed = math.ceil(
            number_of_disbursements or (number_of_transactions / 2)
        )
        logger.info(f"Creating {schedule_b_transactions_needed} Sch B transactions")
        self.locust_data_generator.generate_single_schedule_b_transactions(
            math.ceil(
                schedule_b_transactions_needed
                * single_to_tiered_transaction_ratio
            ),
            reports,
            contacts,
        )
        self.locust_data_generator.generate_tiered_schedule_b_transactions(
            math.ceil(
                schedule_b_transactions_needed
                * (1 - single_to_tiered_transaction_ratio)
            ),
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
