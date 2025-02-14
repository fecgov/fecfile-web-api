from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_report
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form99
from datetime import datetime
from fecfiler.web_services.models import UploadSubmission
import structlog

logger = structlog.get_logger(__name__)


class DotFECForm99TestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")

        self.f99 = create_form99(
            self.committee,
            {"text_code": "TEXT CODE"},
        )
        self.f99.committee_name = "TEST_COMMITTEE"
        # Setup Address
        self.f99.street_1 = "1234 E Test Rd"
        self.f99.street_2 = "Apt 1"
        self.f99.city = "Phoenix"
        self.f99.state = "AZ"
        self.f99.zip = "85018"

        # Setup Treasurer
        self.f99.treasurer_last_name = "Lastname"
        self.f99.treasurer_first_name = "Firstname"
        self.f99.treasurer_middle_name = "Middlename"
        self.f99.treasurer_prefix = "Mr."
        self.f99.treasurer_suffix = "Junior"
        self.f99.save()
        UploadSubmission.objects.initiate_submission(self.f99.id)
        self.f99.refresh_from_db()

        report = compose_report(self.f99.id)
        report_row = serialize_instance(report.get_form_name(), report)
        self.split_row = report_row.split(FS_STR)

    def test_form_type(self):
        self.assertEqual(self.f99.form_type, "F99")
        self.assertEqual(self.split_row[0], "F99")

    def test_committee_id(self):
        self.assertEqual(self.split_row[1], "C00000000")
        self.assertEqual(self.split_row[2], "TEST_COMMITTEE")

    def test_address(self):
        self.assertEqual(self.split_row[3], "1234 E Test Rd")
        self.assertEqual(self.split_row[4], "Apt 1")
        self.assertEqual(self.split_row[5], "Phoenix")
        self.assertEqual(self.split_row[6], "AZ")
        self.assertEqual(self.split_row[7], "85018")

    def test_treasurer(self):
        self.assertEqual(self.split_row[8], "Lastname")
        self.assertEqual(self.split_row[9], "Firstname")
        self.assertEqual(self.split_row[10], "Middlename")
        self.assertEqual(self.split_row[11], "Mr.")
        self.assertEqual(self.split_row[12], "Junior")

    def test_date_signed(self):
        """Because date_signed is timezoned to the server
        the test date needs to be in the same timezone"""
        today = datetime.now()
        formatted_date = today.strftime("%Y%m%d")
        self.assertEqual(self.split_row[13], formatted_date)

    def test_text_code(self):
        self.assertEqual(self.split_row[14], "TEXT CODE")
