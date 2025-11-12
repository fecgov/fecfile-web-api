from django.test import TestCase
from fecfiler.settings import MOCK_OPENFEC_REDIS_URL
import redis
import json

from fecfiler.user.models import User
from fecfiler.contacts.tests.utils import create_test_individual_contact
from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.committee_accounts.utils.data import dump_committee_data
from fecfiler.reports.tests.utils import (
    create_form3x,
    create_form24,
    create_form1m,
    create_form99,
    create_report_memo,
)
from fecfiler.cash_on_hand.tests.utils import create_cash_on_hand_yearly
from fecfiler.transactions.tests.utils import create_schedule_a, create_transaction_memo
from fecfiler.web_services.models import WebPrintSubmission, UploadSubmission, DotFEC


COMMITTEE_ONE_ID = "C10000001"
COMMITTEE_TWO_ID = "C20000002"


class DumpTestDataCommandTest(TestCase):
    def setUp(self):
        self.redis_instance = redis.Redis.from_url(MOCK_OPENFEC_REDIS_URL)
        self.committee = CommitteeAccount.objects.create(committee_id=COMMITTEE_ONE_ID)
        self.committee_two = CommitteeAccount.objects.create(
            committee_id=COMMITTEE_TWO_ID
        )
        self.user = User.objects.create(
            email="tester@fake.gov", first_name="Tester", last_name="Testerson"
        )
        Membership.objects.create(committee_account=self.committee, user=self.user)

    def get_committee_data(self, committee_id=COMMITTEE_ONE_ID):
        dump_committee_data(committee_id, True)
        return json.loads(self.redis_instance.get(f"dumped_data_for_{committee_id}.json"))

    def test_dump_user_data(self):
        committee_data = self.get_committee_data()
        raw_committee_data = json.dumps(committee_data)

        self.assertEqual(len(committee_data), 3)
        self.assertTrue("user.user" in raw_committee_data)
        self.assertTrue("committee_accounts.committeeaccount" in raw_committee_data)
        self.assertTrue("committee_accounts.membership" in raw_committee_data)

        # the next two get masked so can't be checked against raw_committee_data
        self.assertIsNotNone(self.user.first_name)
        self.assertIsNotNone(self.user.last_name)

        self.test_dump_second_committee()

    def test_dump_report_data(self):
        report = create_form3x(self.committee, "20240101", "20240331", {}, "Q1")
        create_form1m(self.committee)
        create_form24(self.committee)
        create_form99(self.committee)
        create_report_memo(self.committee, report, "REPORT_MEMO")
        create_cash_on_hand_yearly(self.committee, 2024, 20125.21)

        committee_data = self.get_committee_data()
        raw_committee_data = json.dumps(committee_data)

        self.assertEqual(len(committee_data), 13)
        self.assertTrue("REPORT_MEMO" in raw_committee_data)
        self.assertTrue("Q1" in raw_committee_data)
        self.assertTrue("20125.21" in raw_committee_data)
        self.test_dump_second_committee()

    def test_dump_transaction_data(self):
        contact = create_test_individual_contact("LAST", "FIRST", self.committee.id)
        report = create_form3x(self.committee, "20240101", "20240331", {}, "Q1")
        transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            contact,
            "20240215",
            223.41,
            report=report,
            purpose_description="PURPOSE",
        )
        create_transaction_memo(self.committee, transaction, "TRANSACTION_MEMO")

        committee_data = self.get_committee_data()
        raw_committee_data = json.dumps(committee_data)

        self.assertEqual(len(committee_data), 10)
        self.assertTrue("PURPOSE" in raw_committee_data)
        self.assertTrue("TRANSACTION_MEMO" in raw_committee_data)
        self.test_dump_second_committee()

    def test_dump_submission_data(self):
        report = create_form3x(self.committee, "20240101", "20240331", {}, "Q1")
        dotfec = DotFEC.objects.create(report=report)
        WebPrintSubmission.objects.create(dot_fec=dotfec)
        UploadSubmission.objects.create(dot_fec=dotfec)

        committee_data = self.get_committee_data()

        self.assertEqual(len(committee_data), 8)
        self.test_dump_second_committee()

    # Ensure that there is no spillover into a second committee
    def test_dump_second_committee(self):
        dump_committee_data(COMMITTEE_TWO_ID, True)
        committee_data = self.get_committee_data(committee_id=COMMITTEE_TWO_ID)

        self.assertEqual(len(committee_data), 1)

    def test_dump_invalid_committee(self):
        self.assertRaises(
            RuntimeError, dump_committee_data, "C30000003", True
        )

    def test_dump_no_committee_id(self):
        self.assertRaises(RuntimeError, dump_committee_data, "", True)
