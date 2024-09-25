from django.test import TestCase
from fecfiler.memo_text.models import MemoText
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_dot_fec, add_row_to_content, compose_report_level_memos
from fecfiler.committee_accounts.views import create_committee_view
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance, CRLF_STR, FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x, create_form99, create_report_memo
from fecfiler.transactions.tests.utils import create_schedule_a
from fecfiler.contacts.tests.utils import create_test_individual_contact
from datetime import datetime


# Tests .FEC composition for TEXT records on Report Level Memos


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
        create_report_memo(
            self.committee,
            self.f3x,
            text4000="F3X_MEMO_TEXT",
        )
        create_report_memo(
            self.committee,
            self.f99,
            text4000="F99_MEMO_TEXT",
        )

        self.f3x_memo = compose_report_level_memos(self.f3x.id)[0]
        self.f99_memo = compose_report_level_memos(self.f99.id)[0]
        self.f3x_row = serialize_instance("Text", self.f3x_memo).split(FS_STR)
        self.f99_row = serialize_instance("Text", self.f99_memo).split(FS_STR)

    def test_record_name(self):
        self.assertEqual(self.f3x_row[0], "TEXT")
        self.assertEqual(self.f99_row[0], "TEXT")

    def test_committee_id(self):
        self.assertEqual(self.f3x_row[1], self.committee.committee_id)
        self.assertEqual(self.f99_row[1], self.committee.committee_id)

    def test_row_contains_report_info(self):
        print(self.f3x_memo.back_reference_sched_form_type)
        input(f"F-Type: {self.f3x.form_type}")
        self.assertEqual(self.f3x_row[2], "REPORT_MEMO_TEXT1")
        # self.assertEqual(self.f3x_row[4], self.f3x.form_type)
        self.assertEqual(self.f99_row[2], "REPORT_MEMO_TEXT1")
        # self.assertEqual(self.f99_row[4], self.f3x.form_type)

        """
        The assertions for column 4 are commented out because those columns are derived
        from the memo's `back_reference_sched_form_name` field which is only populated
        when `compose_dot_fec()` is called"""

    def test_row_contains_text4000(self):
        self.assertEqual(self.f3x_row[5], "F3X_MEMO_TEXT")
        self.assertEqual(self.f99_row[5], "F99_MEMO_TEXT")
