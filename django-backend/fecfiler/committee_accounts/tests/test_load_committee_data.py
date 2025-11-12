from django.test import TestCase
import os

from fecfiler.contacts.models import Contact
from fecfiler.contacts.views import delete_all_contacts
from fecfiler.contacts.tests.utils import create_test_individual_contact
from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.committee_accounts.utils.data import (
    load_committee_data,
    dump_committee_data,
)
from fecfiler.user.models import User
from fecfiler.reports.models import Report
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.reports.utils.report import delete_all_reports
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.tests.utils import create_schedule_a
import structlog


logger = structlog.get_logger(__name__)


TEST_COMMITTEE_ID = "C10000001"


class DumpTestDataCommandTest(TestCase):
    def setUp(self):
        delete_all_reports(committee_id=TEST_COMMITTEE_ID)
        delete_all_contacts(committee_id=TEST_COMMITTEE_ID)

        self.committee = CommitteeAccount.objects.create(committee_id=TEST_COMMITTEE_ID)
        self.user = User.objects.create(
            email="tester@fake.gov", first_name="Tester", last_name="Testerson"
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
            purpose_description="PURPOSE",
        )

        self.filename = f"dumped_data_for_{TEST_COMMITTEE_ID}.json"
        dump_committee_data(TEST_COMMITTEE_ID)

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
        load_committee_data(str(self.user.id), self.filename)
        self.assertIsNotNone(
            Membership.objects.filter(
                committee_account=self.committee, user=self.user
            ).first()
        )
        self.assertEqual(
            Report.objects.filter(committee_account=self.committee).count(), 1
        )
        self.assertEqual(
            Form3X.objects.filter(report__committee_account=self.committee).count(), 1
        )
        self.assertEqual(
            Transaction.objects.filter(committee_account=self.committee).count(), 1
        )
        self.assertEqual(
            ScheduleA.objects.filter(
                transaction__committee_account=self.committee
            ).count(),
            1,
        )
        self.assertEqual(
            Contact.objects.filter(committee_account=self.committee).count(), 1
        )

    def test_load_with_invalid_user(self):
        self.assertRaises(
            RuntimeError,
            load_committee_data,
            "bad_email@fake.gov",
            self.filename,
        )
