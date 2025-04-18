from django.test import TestCase
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
            },
        )

        self.contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id
        )

    def test_f3x_memo(self):
        f3x_memo = create_report_memo(
            self.committee,
            self.f3x,
            text4000="F3X_MEMO_TEXT",
        )
        f3x_memo_row = serialize_instance("Text", f3x_memo).split(FS_STR)
        # row type is correct
        self.assertEqual(f3x_memo_row[0], "TEXT")
        # committee id is correct for report memo
        self.assertEqual(f3x_memo_row[1], self.committee.committee_id)
        # transaction id is correct for report memo
        self.assertEqual(f3x_memo_row[2], "REPORT_MEMO_TEXT1")
        # backreference to form type is correct
        self.assertEqual(f3x_memo_row[4], self.f3x.form_type)
        # memo content is correct
        self.assertEqual(f3x_memo_row[5], "F3X_MEMO_TEXT")

    def test_f99_memo(self):
        f99_memo = create_report_memo(
            self.committee,
            self.f99,
            text4000="F99_MEMO_TEXT",
        )
        f99_memo_row = serialize_instance("Text", f99_memo).split(FS_STR)
        # row type is correct
        self.assertEqual(f99_memo_row[0], "TEXT")
        # committee id is correct for report memo
        self.assertEqual(f99_memo_row[1], self.committee.committee_id)
        # transaction id is correct for report memo
        self.assertEqual(f99_memo_row[2], "REPORT_MEMO_TEXT1")
        # backreference to form type is correct
        self.assertEqual(f99_memo_row[4], self.f99.form_type)
        # memo content is correct
        self.assertEqual(f99_memo_row[5], "F99_MEMO_TEXT")

    def test_transaction_memo(self):
        """create a transaction and memo
        set the form type of the transaction to SA11AII (unitemized)
        but mark the transaction as itemized.  The queryset used should spit out
        a form type of SA11AI (itemized) instead of SA11AII
        This is important to test because if the correct queryset isn't used
        the form type in the memo will say SA11AII instead of SA11AI
        """
        transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            datetime.strptime("2024-01-03", "%Y-%m-%d"),
            "1.00",
            "GENERAL",
            "SA11AII",
            itemized=True,
        )
        transaction_memo = create_transaction_memo(
            self.committee, transaction, "TRANSACTION_MEMO_TEXT"
        )
        memo_row = serialize_instance("Text", transaction_memo).split(FS_STR)
        # row type is correct
        self.assertEqual(memo_row[0], "TEXT")
        # Test committee ID
        self.assertEqual(memo_row[1], self.committee.committee_id)
        # transaction id is correct for transaction memo
        self.assertEqual(memo_row[2], transaction_memo.transaction_id_number)
        # backreference to transaction is correct
        self.assertEqual(memo_row[3], transaction.transaction_id)
        # backreference to form type is correct
        self.assertEqual(memo_row[4], "SA11AI")
        # memo content is correct
        self.assertEqual(memo_row[5], "TRANSACTION_MEMO_TEXT")
