from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_report
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.reports.tests.utils import create_form24
from datetime import datetime, timezone
from fecfiler.web_services.models import UploadSubmission
import structlog

logger = structlog.get_logger(__name__)


class DotFECForm24TestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)

        self.f24 = create_form24(
            self.committee,
            {
                "report_type_24_48": "24",
                "original_amendment_date": datetime.strptime("2024-01-01", "%Y-%m-%d"),
            },
        )
        self.f24.committee_name = "TEST_COMMITTEE"
        # Setup Address
        self.f24.street_1 = "1234 E Test Rd"
        self.f24.street_2 = "Apt 1"
        self.f24.city = "Phoenix"
        self.f24.state = "AZ"
        self.f24.zip = "85018"

        # Setup Treasurer
        self.f24.treasurer_last_name = "Lastname"
        self.f24.treasurer_first_name = "Firstname"
        self.f24.treasurer_middle_name = "Middlename"
        self.f24.treasurer_prefix = "Mr."
        self.f24.treasurer_suffix = "Junior"
        self.f24.save()

        UploadSubmission.objects.initiate_submission(self.f24.id)
        self.f24.refresh_from_db()

        report = compose_report(self.f24.id)
        report_row = serialize_instance(report.get_form_name(), report)
        self.split_row = report_row.split(FS_STR)

    def test_form_type(self):
        self.assertEqual(self.f24.form_type, "F24N")
        for row in self.split_row:
            logger.debug(row)
        self.assertEqual(self.split_row[0], "F24N")
        self.assertEqual(self.split_row[2], "24")
        self.assertEqual(self.split_row[3], "20240101")

    def test_committee_id(self):
        self.assertEqual(self.split_row[1], "C00000000")
        self.assertEqual(self.split_row[4], "TEST_COMMITTEE")

    def test_address(self):
        self.assertEqual(self.split_row[5], "1234 E Test Rd")
        self.assertEqual(self.split_row[6], "Apt 1")
        self.assertEqual(self.split_row[7], "Phoenix")
        self.assertEqual(self.split_row[8], "AZ")
        self.assertEqual(self.split_row[9], "85018")

    def test_treasurer(self):
        self.assertEqual(self.split_row[10], "Lastname")
        self.assertEqual(self.split_row[11], "Firstname")
        self.assertEqual(self.split_row[12], "Middlename")
        self.assertEqual(self.split_row[13], "Mr.")
        self.assertEqual(self.split_row[14], "Junior")

    def test_date_signed(self):
        """Because date_signed is timezoned to the server
        the test date needs to be in the same timezone"""
        today = datetime.now()
        formatted_date = today.strftime("%Y%m%d")
        self.assertEqual(self.split_row[15], formatted_date)
