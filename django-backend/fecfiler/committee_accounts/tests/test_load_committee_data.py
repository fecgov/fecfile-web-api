from django.test import TestCase
from django.core.management.base import CommandError
from django.core.management import call_command
import os

from fecfiler.reports.views import delete_all_reports
from fecfiler.contacts.views import delete_all_contacts

from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.user.models import User
from fecfiler.contacts.tests.utils import create_test_individual_contact
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.tests.utils import (
    create_schedule_a, create_transaction_memo
)
from fecfiler.reports.models import Report
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.contacts.models import Contact
from fecfiler.memo_text.models import MemoText
import structlog


logger = structlog.get_logger(__name__)


TEST_COMMITTEE_ID = "C10000001"


class DumpTestDataCommandTest(TestCase):
    def setUp(self):
        delete_all_reports(committee_id=TEST_COMMITTEE_ID)
        delete_all_contacts(committee_id=TEST_COMMITTEE_ID)

        self.committee = CommitteeAccount.objects.create(committee_id=TEST_COMMITTEE_ID)
        self.user = User.objects.create(
            email="tester@fake.gov",
            first_name="Tester",
            last_name="Testerson"
        )

        self.contact = create_test_individual_contact("LAST", "FIRST", self.committee.id)
        self.report = create_form3x(self.committee, "20240101", "20240331", {}, "Q1")
        self.transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact,
            "20240215",
            223.41,
            report=self.report,
            purpose_description="PURPOSE"
        )

        self.filename = f"dumped_data_for_{TEST_COMMITTEE_ID}.json"
        call_command("dump_committee_data", TEST_COMMITTEE_ID)

        delete_all_reports(committee_id=TEST_COMMITTEE_ID)
        delete_all_contacts(committee_id=TEST_COMMITTEE_ID)

    def tearDown(self):
        delete_all_reports(committee_id=TEST_COMMITTEE_ID)
        delete_all_contacts(committee_id=TEST_COMMITTEE_ID)
        if os.path.isfile(self.filename):
            logger.info("Cleaning up after testing loading committee data...")
            logger.info(f"Removing generated file: {self.filename}...")
            os.remove(self.filename)
            logger.info("Successfully removed file")

    def test_load_user_data(self):
        call_command("load_committee_data", self.filename, self.user.id)
        self.assertIsNotNone(
            Membership.objects.filter(
                committee_account=self.committee,
                user=self.user
            ).first()
        )
        self.assertEqual(
            Report.objects.filter(
                committee_account=self.committee
            ).count(),
            1
        )
        self.assertEqual(
            Form3X.objects.filter(
                report__committee_account=self.committee
            ).count(),
            1
        )
        self.assertEqual(
            Transaction.objects.filter(
                committee_account=self.committee
            ).count(),
            1
        )
        self.assertEqual(
            ScheduleA.objects.filter(
                transaction__committee_account=self.committee
            ).count(),
            1
        )
        self.assertEqual(
            Contact.objects.filter(
                committee_account=self.committee
            ).count(),
            1
        )

    def test_load_with_invalid_user(self):
        self.assertRaises(
            CommandError,
            call_command,
            "load_committee_data", self.filename, "bad_email@fake.gov"
        )
