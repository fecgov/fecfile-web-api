from unittest.mock import patch
from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_composer import (
    compose_dot_fec,
    compose_transaction,
    add_row_to_content,
    compose_header,
)
from fecfiler.web_services.dot_fec.dot_fec_serializer import (
    serialize_instance,
    CRLF_STR,
    FS_STR,
)
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x, create_form99, create_report_memo
from fecfiler.transactions.tests.utils import create_schedule_a, create_loan_from_bank
from fecfiler.contacts.tests.utils import create_test_individual_contact
from django.core.exceptions import ImproperlyConfigured
from datetime import datetime
from decimal import Decimal


class DotFECSerializerTestCase(TestCase):

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
                "filing_frequency": "Q",
                "text_code": "ABC",
                "pdf_attachment": True,
                "message_text": "\nBEHOLD! A large text string\nwith new lines",
            },
        )
        self.contact_1 = create_test_individual_contact(
            "last name",
            "First name",
            self.committee.id,
            {
                "middle_name": "Middle Name",
                "prefix": "Mr.",
                "suffix": "Junior",
                "street_1": "1234 Street Rd",
                "street_2": "Apt 1",
                "city": "Phoenix",
                "state": "MD",
                "zip": "12345",
                "employer": "employer",
                "occupation": "occupation",
            },
        )

        self.transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            datetime.strptime("2024-01-03", "%Y-%m-%d"),
            "1.00",
            "GENERAL",
            "SA11AI",
        )
        self.transaction.reports.add(self.f3x)
        self.transaction.save()
        self.report_level_memo = create_report_memo(
            self.committee,
            self.f3x,
            text4000="dahtest2",
        )

    def test_compose_dot_fec(self):
        with self.assertRaisesMessage(Exception, "header: 100000000 not found"):
            compose_dot_fec(100000000)

        file_content = compose_dot_fec(self.f3x.id)
        self.assertEqual(file_content.count(CRLF_STR), 3)

    def test_add_row_to_content(self):
        summary_row = serialize_instance("F3X", self.f3x)
        dot_fec_str = add_row_to_content(None, summary_row)
        self.assertEqual(dot_fec_str[-2:], CRLF_STR)
        transaction_row = serialize_instance("SchA", self.transaction)
        dot_fec_str = add_row_to_content(dot_fec_str, transaction_row)
        self.assertEqual(dot_fec_str[-2:], CRLF_STR)
        report_level_memo_row = serialize_instance("Text", self.report_level_memo)
        dot_fec_str = add_row_to_content(dot_fec_str, report_level_memo_row)
        self.assertEqual(dot_fec_str[-2:], CRLF_STR)
        split_dot_fec_str = dot_fec_str.split(CRLF_STR)
        self.assertEqual(split_dot_fec_str[0].split(FS_STR)[-1], "381.00")
        self.assertEqual(split_dot_fec_str[1].split(FS_STR)[0], "SA11AI")
        self.assertEqual(split_dot_fec_str[2].split(FS_STR)[-1], "dahtest2")

    def test_row_contains_aggregate(self):
        new_contact = create_test_individual_contact(
            "test last name", "test first name", self.committee.id
        )
        earlier_transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            new_contact,
            datetime.strptime("2024-01-03", "%Y-%m-%d"),
            "50.00",
            "GENERAL",
            "SA11AI",
        )
        later_transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            new_contact,
            datetime.strptime("2024-01-04", "%Y-%m-%d"),
            "25.00",
            "GENERAL",
            "SA11AI",
        )
        for transaction in [earlier_transaction, later_transaction]:
            transaction.reports.add(self.f3x)
            transaction.save()

        later_transaction.refresh_from_db()
        transaction_row = serialize_instance("SchA", later_transaction)
        row_str = add_row_to_content("", transaction_row)
        self.assertIn("75.00", row_str)

    @patch("fecfiler.validation.utilities.FEC_FORMAT_VERSION", "8.5")
    def test_f99(self):
        content = compose_dot_fec(self.f99.id)
        split_content = content.split(CRLF_STR)
        split_report_row = split_content[1].split(FS_STR)
        self.assertEqual(split_report_row[14], "ABC")
        self.assertEqual(split_report_row[15], "Q")
        self.assertEqual(split_report_row[16], "X")
        self.assertEqual(split_content[2], "[BEGINTEXT]")
        self.assertEqual(
            split_content[3],
            "\nBEHOLD! A large text string\nwith new lines",
        )
        self.assertEqual(split_content[4], "[ENDTEXT]")

    @patch("fecfiler.web_services.dot_fec.dot_fec_composer.FEC_FORMAT_VERSION", None)
    def test_missing_fec_format_version_raises_error(self):
        with self.assertRaises(ImproperlyConfigured) as cm:
            compose_header(self.f3x.id)
        self.assertIn("FEC_FORMAT_VERSION is not set", str(cm.exception))

    @patch("fecfiler.validation.utilities.FEC_FORMAT_VERSION", "8.4")
    def test_schema_override_8_dot_4_f99(self):
        content = compose_dot_fec(self.f99.id)
        split_content = content.split(CRLF_STR)
        split_report_row = split_content[1].split(FS_STR)
        self.assertEqual(split_report_row[14], "ABC")
        self.assertEqual(len(split_report_row), 15)

    @patch("fecfiler.validation.utilities.FEC_FORMAT_VERSION", "8.4")
    def test_schema_override_8_dot_4_C2(self):
        _, _, _, c2 = create_loan_from_bank(
            self.committee,
            self.contact_1,
            1000.00,
            datetime.strptime("2024-01-10", "%Y-%m-%d"),
            "5%",
            loan_incurred_date=datetime.strptime("2024-01-02", "%Y-%m-%d"),
            report=self.f3x,
        )
        c2.schedule_c2.guaranteed_amount = Decimal(10.00)
        c2.schedule_c2.save()
        c2.refresh_from_db()
        compose_transaction(c2)
        content = serialize_instance("SchC2", c2)
        split_content = content.split(FS_STR)
        self.assertEqual(split_content[0], "SC2/10")
        self.assertEqual(split_content[4], self.contact_1.last_name)
        self.assertEqual(split_content[5], self.contact_1.first_name)
        self.assertEqual(split_content[6], self.contact_1.middle_name)
        self.assertEqual(split_content[7], self.contact_1.prefix)
        self.assertEqual(split_content[8], self.contact_1.suffix)
        self.assertEqual(split_content[9], self.contact_1.street_1)
        self.assertEqual(split_content[10], self.contact_1.street_2)
        self.assertEqual(split_content[11], self.contact_1.city)
        self.assertEqual(split_content[12], self.contact_1.state)
        self.assertEqual(split_content[13], self.contact_1.zip)
        self.assertEqual(split_content[14], self.contact_1.employer)
        self.assertEqual(split_content[15], self.contact_1.occupation)
        self.assertEqual(split_content[16], "10.00")
