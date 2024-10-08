from django.test import TestCase
from fecfiler.committee_accounts.views import create_committee_view
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance, FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x, create_form99, create_report_memo
from fecfiler.transactions.tests.utils import create_schedule_a, create_transaction_memo
from fecfiler.contacts.tests.utils import create_test_individual_contact
from datetime import datetime


# Tests .FEC composition for TEXT records on MemoTexts for reports and transactions


class DotFECTextRecordsTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
        coverage_from = datetime.strptime("2024-01-01", "%Y-%m-%d")
        coverage_through = datetime.strptime("2024-02-01", "%Y-%m-%d")
        self.f3x = create_form3x(
            self.committee,
            coverage_from,
            coverage_through,
            {"L38_net_operating_expenditures_ytd": format(381.00, ".2f")},
        )
        self.f99 = create_form99(
            self.committee,
            {
                "text_code": "ABC",
                "message_text": "\nBEHOLD! A large text string\nwith new lines",
            }
        )

        contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id
        )
        self.transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            contact_1,
            datetime.strptime("2024-01-03", "%Y-%m-%d"),
            "1.00",
            "GENERAL",
            "SA11AI",
        )

        self.f3x_memo = create_report_memo(
            self.committee,
            self.f3x,
            text4000="F3X_MEMO_TEXT",
        )
        self.f99_memo = create_report_memo(
            self.committee,
            self.f99,
            text4000="F99_MEMO_TEXT",
        )
        self.transaction_memo = create_transaction_memo(
            self.committee,
            self.transaction,
            "TRANSACTION_MEMO_TEXT"
        )

        self.f3x_row = serialize_instance("Text", self.f3x_memo).split(FS_STR)
        self.f99_row = serialize_instance("Text", self.f99_memo).split(FS_STR)
        self.transaction_row = serialize_instance(
            "Text",
            self.transaction_memo
        ).split(FS_STR)

    def test_record_name(self):
        self.assertEqual(self.f3x_row[0], "TEXT")
        self.assertEqual(self.f99_row[0], "TEXT")
        self.assertEqual(self.transaction_row[0], "TEXT")

    def test_committee_id(self):
        self.assertEqual(self.f3x_row[1], self.committee.committee_id)
        self.assertEqual(self.f99_row[1], self.committee.committee_id)
        self.assertEqual(self.transaction_row[1], self.committee.committee_id)

    def test_row_contains_report_info(self):
        self.assertEqual(self.f3x_row[2], "REPORT_MEMO_TEXT1")
        self.assertEqual(self.f3x_row[4], self.f3x.form_type)
        self.assertEqual(self.f99_row[2], "REPORT_MEMO_TEXT1")
        self.assertEqual(self.f99_row[4], self.f99.form_type)

    def test_row_contains_transaction_info(self):
        self.assertEqual(self.transaction_row[3], self.transaction.transaction_id)
        self.assertEqual(self.transaction_row[4], self.transaction.form_type)

    def test_row_contains_text4000(self):
        self.assertEqual(self.f3x_row[5], "F3X_MEMO_TEXT")
        self.assertEqual(self.f99_row[5], "F99_MEMO_TEXT")
        self.assertEqual(self.transaction_row[5], "TRANSACTION_MEMO_TEXT")