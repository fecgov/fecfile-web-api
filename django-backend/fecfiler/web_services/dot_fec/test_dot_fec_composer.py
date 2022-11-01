from django.test import TestCase
from curses import ascii
from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.scha_transactions.models import SchATransaction
from .dot_fec_composer import compose_dot_fec, add_row_to_content
from .dot_fec_serializer import serialize_model_instance, CRLF_STR


class DotFECSerializerTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_individual_receipt",
        "test_memo_text"
    ]

    def setUp(self):
        self.f3x = F3XSummary.objects.filter(
            id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae"
        ).first()
        self.transaction = SchATransaction.objects.filter(
            id="e7880981-9ee7-486f-b288-7a607e4cd0dd"
        ).first()

    def test_compose_dot_fec(self):
        with self.assertRaisesMessage(Exception, "report: 100000000 not found"):
            compose_dot_fec(100000000, None)

        file_content = compose_dot_fec("b6d60d2d-d926-4e89-ad4b-c47d152a66ae", None)
        self.assertEqual(file_content.count(CRLF_STR), 3)

    def test_add_row_to_content(self):
        summary_row = serialize_model_instance("F3X", F3XSummary, self.f3x)
        dot_fec_str = add_row_to_content(None, summary_row)
        self.assertEqual(dot_fec_str[-2:], CRLF_STR)
        transaction_row = serialize_model_instance(
            "SchA", SchATransaction, self.transaction
        )
        dot_fec_str = add_row_to_content(dot_fec_str, transaction_row)
        self.assertEqual(dot_fec_str[-2:], CRLF_STR)
        split_dot_fec_str = dot_fec_str.split(CRLF_STR)
        self.assertEqual(split_dot_fec_str[0].split(chr(ascii.FS))[-1], "381.00")
        self.assertEqual(split_dot_fec_str[1].split(chr(ascii.FS))[0], "SA11AI")
