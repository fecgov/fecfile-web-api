from django.test import TestCase
from fecfiler.reports.models import Report
from fecfiler.memo_text.models import MemoText
from fecfiler.transactions.models import Transaction
from .dot_fec_composer import compose_dot_fec, add_row_to_content
from fecfiler.committee_accounts.views import create_committee_view
from .dot_fec_serializer import serialize_instance, CRLF_STR, FS_STR


class DotFECSerializerTestCase(TestCase):
    fixtures = [
        "C01234567_user_and_committee",
        "test_f3x_reports",
        "test_f99",
        "test_individual_receipt",
        "test_memo_text",
    ]

    def setUp(self):
        create_committee_view("11111111-2222-3333-4444-555555555555")
        self.f3x = Report.objects.filter(
            id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae"
        ).first()
        self.transaction = Transaction.objects.filter(
            id="e7880981-9ee7-486f-b288-7a607e4cd0dd"
        ).first()
        self.report_level_memo_text = MemoText.objects.filter(
            id="1dee28f8-4cfa-4f70-8658-7a9e7f02ab1d"
        ).first()

    def test_compose_dot_fec(self):
        with self.assertRaisesMessage(Exception, "header: 100000000 not found"):
            compose_dot_fec(100000000, None)

        file_content = compose_dot_fec("b6d60d2d-d926-4e89-ad4b-c47d152a66ae", None)
        self.assertEqual(file_content.count(CRLF_STR), 5)

    def test_add_row_to_content(self):
        summary_row = serialize_instance("F3X", self.f3x)
        dot_fec_str = add_row_to_content(None, summary_row)
        self.assertEqual(dot_fec_str[-2:], CRLF_STR)
        transaction_row = serialize_instance("SchA", self.transaction)
        dot_fec_str = add_row_to_content(dot_fec_str, transaction_row)
        self.assertEqual(dot_fec_str[-2:], CRLF_STR)
        report_level_memo_row = serialize_instance("Text", self.report_level_memo_text)
        dot_fec_str = add_row_to_content(dot_fec_str, report_level_memo_row)
        self.assertEqual(dot_fec_str[-2:], CRLF_STR)
        split_dot_fec_str = dot_fec_str.split(CRLF_STR)
        self.assertEqual(split_dot_fec_str[0].split(FS_STR)[-1], "381.00")
        self.assertEqual(split_dot_fec_str[1].split(FS_STR)[0], "SA11AI")
        self.assertEqual(split_dot_fec_str[2].split(FS_STR)[-1], "dahtest2")

    def test_f99(self):
        content = compose_dot_fec("11111111-1111-1111-1111-111111111111", None)
        split_content = content.split("\n")
        split_report_row = split_content[1].split(FS_STR)
        self.assertEqual(split_report_row[14], "ABC\r")
        free_text = content[content.find("[BEGINTEXT]") :]
        self.assertEqual(
            free_text,
            "[BEGINTEXT]\r\n\nBEHOLD! A large text string"
            + "\nwith new lines\r\n[ENDTEXT]\r\n",
        )
