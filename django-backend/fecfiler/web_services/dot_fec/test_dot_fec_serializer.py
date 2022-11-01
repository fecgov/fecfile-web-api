from django.test import TestCase
from .dot_fec_serializer import (
    serialize_field,
    serialize_model_instance,
)
from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.memo_text.models import MemoText
from fecfiler.scha_transactions.models import SchATransaction
from curses import ascii


class DotFECSerializerTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_individual_receipt",
        "test_memo_text",
        "test_memo_text"
    ]

    def setUp(self):
        self.f3x = F3XSummary.objects.filter(
            id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae"
        ).first()
        self.transaction = SchATransaction.objects.filter(
            id="e7880981-9ee7-486f-b288-7a607e4cd0dd"
        ).first()
        self.report_level_memo_text = MemoText.objects.filter(
            id="1dee28f8-4cfa-4f70-8658-7a9e7f02ab1d"
        ).first()

    def test_serialize_field(self):
        # TEXT
        serialized_text = serialize_field(F3XSummary, self.f3x, "treasurer_last_name")
        self.assertEquals(serialized_text, "Lastname")
        serialized_text_undefined = serialize_field(
            F3XSummary, F3XSummary(), "treasurer_last_name"
        )
        self.assertEquals(serialized_text_undefined, "")

        # NUMERIC
        serialized_numeric = serialize_field(
            F3XSummary, self.f3x, "L6b_cash_on_hand_beginning_period"
        )
        self.assertEqual(serialized_numeric, "6.00")
        serialized_numeric_undefined = serialize_field(
            F3XSummary, F3XSummary(), "L6b_cash_on_hand_beginning_period"
        )
        self.assertEqual(serialized_numeric_undefined, "")

        # DECIMAL
        serialized_decimal = serialize_field(
            SchATransaction, self.transaction, "contribution_amount"
        )
        self.assertEqual(serialized_decimal, "1234.56")
        serialized_decimal_undefined = serialize_field(
            SchATransaction, SchATransaction(), "contribution_amount"
        )
        self.assertEqual(serialized_decimal_undefined, "")

        # DATE
        serialzed_date = serialize_field(F3XSummary, self.f3x, "date_signed")
        self.assertEqual(serialzed_date, "20040729")
        serialzed_date_undefined = serialize_field(
            F3XSummary, F3XSummary(), "date_signed"
        )
        self.assertEqual(serialzed_date_undefined, "")

        # BOOLEAN
        serialized_boolean_true = serialize_field(
            F3XSummary, self.f3x, "change_of_address"
        )
        self.assertEqual(serialized_boolean_true, "X")
        serialized_boolean_false = serialize_field(
            F3XSummary, self.f3x, "qualified_committee"
        )
        self.assertEqual(serialized_boolean_false, "")
        serialized_boolean_undefined = serialize_field(
            F3XSummary, F3XSummary(), "qualified_committee"
        )
        self.assertEqual(serialized_boolean_undefined, "")

        # FOREIGN KEY
        serialized_foreign_key = serialize_field(F3XSummary, self.f3x, "report_code")
        self.assertEqual(serialized_foreign_key, "Q1")
        serialized_foreign_key_undefined = serialize_field(
            F3XSummary, F3XSummary(), "report_code"
        )
        self.assertEqual(serialized_foreign_key_undefined, "")

    def test_serialize_f3x_summary(self):
        summary_row = serialize_model_instance("F3X", F3XSummary, self.f3x)
        split_row = summary_row.split(chr(ascii.FS))
        self.assertEqual(split_row[0], "F3XN")
        self.assertEqual(split_row[21], "20040729")
        self.assertEqual(split_row[3], "X")
        self.assertEqual(split_row[122], "381.00")

    def test_serialize_scha_transaction(self):
        transaction_row = serialize_model_instance(
            "SchA", SchATransaction, self.transaction
        )
        split_row = transaction_row.split(chr(ascii.FS))
        self.assertEqual(split_row[0], "SA11AI")

    def test_serialize_report_level_memo(self):
        report_level_memo_row = serialize_model_instance(
            "Text", MemoText, self.report_level_memo_text
        )
        split_row = report_level_memo_row.split(chr(ascii.FS))
        self.assertEqual(split_row[0], "TEXT")
        self.assertEqual(split_row[1], "C00601211")
        self.assertEqual(split_row[2], "REPORT_MEMO_TEXT_1")
        self.assertEqual(split_row[4], "F3XN")
        self.assertEqual(split_row[5], "dahtest2")
