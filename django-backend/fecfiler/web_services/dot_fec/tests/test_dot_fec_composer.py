from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_composer import (
    compose_dot_fec,
    add_row_to_content,
)
from fecfiler.web_services.dot_fec.dot_fec_serializer import (
    serialize_instance,
    CRLF_STR,
    FS_STR,
)
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x, create_form99, create_report_memo
from fecfiler.transactions.tests.utils import create_schedule_a
from fecfiler.contacts.tests.utils import create_test_individual_contact
from datetime import datetime


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
                "text_code": "ABC",
                "message_text": "\nBEHOLD! A large text string\nwith new lines",
            },
        )
        self.contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id
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

    def test_f99(self):
        content = compose_dot_fec(self.f99.id)
        split_content = content.split("\n")
        split_report_row = split_content[1].split(FS_STR)
        self.assertEqual(split_report_row[14], "ABC\r")
        free_text = content[content.find("[BEGINTEXT]") :]
        self.assertEqual(
            free_text,
            "[BEGINTEXT]\r\n\nBEHOLD! A large text string"
            + "\nwith new lines\r\n[ENDTEXT]\r\n",
        )
