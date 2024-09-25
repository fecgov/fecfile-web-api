from django.test import TestCase
from decimal import Decimal
from fecfiler.web_services.dot_fec.dot_fec_serializer import (
    serialize_field,
    serialize_instance,
    get_field_mappings,
    get_value_from_path,
)
from fecfiler.web_services.dot_fec.dot_fec_composer import Header
from fecfiler.reports.models import Report
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.views import create_committee_view
from fecfiler.reports.tests.utils import create_form3x, create_report_memo
from fecfiler.transactions.tests.utils import create_schedule_a, create_loan
from fecfiler.contacts.tests.utils import create_test_individual_contact
from datetime import datetime, date


class DotFECSerializerTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
        coverage_from = datetime.strptime("2024-01-01", "%Y-%m-%d")
        coverage_through = datetime.strptime("2024-02-01", "%Y-%m-%d")
        self.f3x = create_form3x(
            self.committee,
            coverage_from,
            coverage_through,
            {
                "L38_net_operating_expenditures_ytd": format(381.00, ".2f"),
                "L6b_cash_on_hand_beginning_period": format(6.00, ".2f"),
                "change_of_address": True,
            },
        )
        self.f3x.treasurer_last_name = "Lastname"
        self.f3x.date_signed = datetime.strptime("2004-07-29", "%Y-%m-%d")

        self.f3x.save()

        self.contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id
        )

        self.transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            datetime.strptime("2020-04-19", "%Y-%m-%d"),
            "1234.56",
            "GENERAL",
            "SA11AI",
        )
        self.transaction.reports.add(self.f3x)
        self.transaction.save()

        self.schc_transaction1 = create_loan(
            self.committee,
            self.contact_1,
            10,
            datetime.strptime("2023-09-20", "%Y-%m-%d"),
            "2.0",
            True,
        )

        self.schc_transaction2 = create_loan(
            self.committee,
            self.contact_1,
            10,
            datetime.strptime("2023-09-20", "%Y-%m-%d"),
            "2.0",
        )

        self.report_level_memo_text = create_report_memo(
            self.committee,
            self.f3x,
            "dahtest2"
        )

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
            Report(), "treasurer_last_name", f3x_field_mappings
        )
        self.assertEquals(serialized_text_undefined, "")

        # NUMERIC
        serialized_numeric = serialize_field(
            self.f3x, "L6b_cash_on_hand_beginning_period", f3x_field_mappings
        )
        self.assertEqual(serialized_numeric, "6.00")
        self.f3x.form_3x.L6b_cash_on_hand_beginning_period = Decimal("0.00")
        serialized_numeric_0 = serialize_field(  # 0.00 should be serialized as 0.00
            self.f3x, "L6b_cash_on_hand_beginning_period", f3x_field_mappings
        )
        self.assertEqual(serialized_numeric_0, "0.00")
        serialized_numeric_undefined = (
            serialize_field(  # undefined should be serialized as ""
                Report(), "L6b_cash_on_hand_beginning_period", f3x_field_mappings
            )
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
            Report(), "date_signed", f3x_field_mappings
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
            Report(), "qualified_committee", f3x_field_mappings
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
        self.assertEqual(self.f3x.form_type, "F3XN")
        summary_row = serialize_instance("F3X", self.f3x)
        split_row = summary_row.split(FS_STR)
        self.assertEqual(split_row[0], "F3XN")
        self.assertEqual(split_row[21], "20040729")
        self.assertEqual(split_row[3], "X")
        self.assertEqual(split_row[122], "381.00")

    def test_serialize_schedule_a_transaction_instance(self):
        transaction_row = serialize_instance("SchA", self.transaction)
        split_row = transaction_row.split(FS_STR)
        self.assertEqual(split_row[0], "SA11AI")

    def test_serialize_report_level_memo_instance(self):
        report_level_memo_row = serialize_instance("Text", self.report_level_memo_text)
        split_row = report_level_memo_row.split(FS_STR)
        self.assertEqual(split_row[0], "TEXT")
        self.assertEqual(split_row[1], "C00000000")
        self.assertEqual(split_row[2], "REPORT_MEMO_TEXT1")
        self.assertEqual(split_row[4], "F3XN")
        self.assertEqual(split_row[5], "dahtest2")

    def test_serialize_header_instance(self):
        report_level_memo_row = serialize_instance("HDR", self.header)
        split_row = report_level_memo_row.split(FS_STR)
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
        self.assertEqual(contribution_date.date(), date(2020, 4, 19))
        bogus_value = get_value_from_path(self.transaction, "not.real.path")
        self.assertIsNone(bogus_value)
