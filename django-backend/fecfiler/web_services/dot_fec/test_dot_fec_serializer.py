from django.test import TestCase
import datetime
from .dot_fec_serializer import (
    serialize_field,
    serialize_instance,
    get_field_mappings,
    get_value_from_path,
)
from .dot_fec_composer import Header
from fecfiler.reports.f3x_report.models import F3XReport
from fecfiler.memo_text.models import MemoText
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from curses import ascii


class DotFECSerializerTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_individual_receipt",
        "test_memo_text",
        "test_fake_schedule_c",
    ]

    def setUp(self):
        self.f3x = F3XReport.objects.filter(
            id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae"
        ).first()
        self.transaction = Transaction.objects.filter(
            id="e7880981-9ee7-486f-b288-7a607e4cd0dd"
        ).first()
        self.schc_transaction1 = Transaction.objects.filter(
            id="57b95c3a-f7bc-4c36-a3fd-66bb52976eec"
        ).first()
        self.schc_transaction2 = Transaction.objects.filter(
            id="3fce473a-7939-4733-a0a8-298d16a058cd"
        ).first()
        self.report_level_memo_text = MemoText.objects.filter(
            id="1dee28f8-4cfa-4f70-8658-7a9e7f02ab1d"
        ).first()
        self.report_level_memo_text.filer_committee_id_number = "C00601211"
        self.report_level_memo_text.back_reference_sched_form_name = "F3XN"
        self.header = Header("HDR", "FEC", "8.4", "FECFile Online", "0.0.1")

    def test_serialize_field(self):
        f3x_field_mappings = get_field_mappings("F3X")
        schc_field_mappings = get_field_mappings("SchC")
        # TEXT
        serialized_text = serialize_field(
            self.f3x, "treasurer_last_name", f3x_field_mappings
        )
        self.assertEquals(serialized_text, "Lastname")
        serialized_text_undefined = serialize_field(
            F3XReport(), "treasurer_last_name", f3x_field_mappings
        )
        self.assertEquals(serialized_text_undefined, "")

        # NUMERIC
        serialized_numeric = serialize_field(
            self.f3x, "L6b_cash_on_hand_beginning_period", f3x_field_mappings
        )
        self.assertEqual(serialized_numeric, "6.00")
        serialized_numeric_undefined = serialize_field(
            F3XReport(), "L6b_cash_on_hand_beginning_period", f3x_field_mappings
        )
        self.assertEqual(serialized_numeric_undefined, "")

        # DECIMAL
        scha_field_mappings = get_field_mappings("SchA")
        serialized_decimal = serialize_field(
            self.transaction, "contribution_amount", scha_field_mappings
        )
        self.assertEqual(serialized_decimal, "1234.56")
        transaction = Transaction()
        transaction.schedule_a = ScheduleA()
        serialized_decimal_undefined = serialize_field(
            transaction, "contribution_amount", scha_field_mappings
        )
        self.assertEqual(serialized_decimal_undefined, "")

        # DATE
        serialzed_date = serialize_field(self.f3x, "date_signed", f3x_field_mappings)
        self.assertEqual(serialzed_date, "20040729")
        serialzed_date_undefined = serialize_field(
            F3XReport(), "date_signed", f3x_field_mappings
        )
        self.assertEqual(serialzed_date_undefined, "")

        # BOOLEAN_X
        serialized_boolean_x_true = serialize_field(
            self.f3x, "change_of_address", f3x_field_mappings
        )
        self.assertEqual(serialized_boolean_x_true, "X")
        serialized_boolean_x_false = serialize_field(
            self.f3x, "qualified_committee", f3x_field_mappings
        )
        self.assertEqual(serialized_boolean_x_false, "")
        serialized_boolean_x_undefined = serialize_field(
            F3XReport(), "qualified_committee", f3x_field_mappings
        )
        self.assertEqual(serialized_boolean_x_undefined, "")

        # BOOLEAN_YN
        serialized_boolean_yn_true = serialize_field(
            self.schc_transaction1, "secured", schc_field_mappings
        )
        self.assertEqual(serialized_boolean_yn_true, "Y")
        serialized_boolean_yn_false = serialize_field(
            self.schc_transaction1, "personal_funds", schc_field_mappings
        )
        self.assertEqual(serialized_boolean_yn_false, "N")
        serialized_boolean_yn_undefined = serialize_field(
            self.schc_transaction2, "personal_funds", schc_field_mappings
        )
        # N Because model has default=False, otherwise would be ''
        self.assertEqual(serialized_boolean_yn_undefined, "N")

    def test_serialize_f3x_summary_instance(self):
        summary_row = serialize_instance("F3X", self.f3x)
        split_row = summary_row.split(chr(ascii.FS))
        self.assertEqual(split_row[0], "F3XN")
        self.assertEqual(split_row[21], "20040729")
        self.assertEqual(split_row[3], "X")
        self.assertEqual(split_row[122], "381.00")

    def test_serialize_schedule_a_transaction_instance(self):
        transaction_row = serialize_instance("SchA", self.transaction)
        split_row = transaction_row.split(chr(ascii.FS))
        self.assertEqual(split_row[0], "SA11AI")

    def test_serialize_report_level_memo_instance(self):
        report_level_memo_row = serialize_instance("Text", self.report_level_memo_text)
        split_row = report_level_memo_row.split(chr(ascii.FS))
        self.assertEqual(split_row[0], "TEXT")
        self.assertEqual(split_row[1], "C00601211")
        self.assertEqual(split_row[2], "REPORT_MEMO_TEXT_1")
        self.assertEqual(split_row[4], "F3XN")
        self.assertEqual(split_row[5], "dahtest2")

    def test_serialize_header_instance(self):
        report_level_memo_row = serialize_instance("HDR", self.header)
        split_row = report_level_memo_row.split(chr(ascii.FS))
        self.assertEqual(split_row[0], "HDR")
        self.assertEqual(split_row[1], "FEC")
        self.assertEqual(split_row[2], "8.4")
        self.assertEqual(split_row[3], "FECFile Online")
        self.assertEqual(split_row[4], "0.0.1")

    def test_get_value_from_path(self):
        form_type = get_value_from_path(self.transaction, "form_type")
        self.assertEqual(form_type, "SA11AI")
        contribution_date = get_value_from_path(
            self.transaction, "schedule_a.contribution_date"
        )
        self.assertEqual(contribution_date, datetime.date(2020, 4, 19))
        bogus_value = get_value_from_path(self.transaction, "not.real.path")
        self.assertIsNone(bogus_value)
