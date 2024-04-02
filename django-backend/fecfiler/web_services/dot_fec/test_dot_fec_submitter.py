import json
from uuid import uuid4 as uuid
from django.test import TestCase
from .dot_fec_submitter import DotFECSubmitter
from fecfiler.web_services.models import DotFEC
from fecfiler.web_services.tasks import create_dot_fec
from fecfiler.reports.models import Report
from fecfiler.committee_accounts.views import create_committee_view


class DotFECSubmitterTestCase(TestCase):
    fixtures = [
        "C01234567_user_and_committee",
        "test_f3x_reports",
    ]

    def setUp(self):
        create_committee_view("11111111-2222-3333-4444-555555555555")
        self.f3x = Report.objects.filter(
            id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae"
        ).first()
        self.dot_fec_id = create_dot_fec(
            "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            force_write_to_disk=True,
        )
        self.dot_fec_record = DotFEC.objects.get(id=self.dot_fec_id)

    def test_get_submission_json(self):
        submitter = DotFECSubmitter(None)
        json_str = submitter.get_submission_json(
            self.dot_fec_record, "test_json_password"
        )
        json_obj = json.loads(json_str)
        self.assertEqual(json_obj["email_1"], self.f3x.confirmation_email_1)
        self.assertEqual(json_obj["email_2"], self.f3x.confirmation_email_2)
        self.assertFalse(json_obj["wait"])

    def test_get_submission_json_for_amendment(self):
        submitter = DotFECSubmitter(None)
        self.dot_fec_record.report.report_id = str(uuid())
        json_str = submitter.get_submission_json(
            self.dot_fec_record, "test_json_password", "test_backdoor_code"
        )
        json_obj = json.loads(json_str)
        self.assertEqual(
            json_obj["amendment_id"],
            self.dot_fec_record.report.report_id + "test_backdoor_code",
        )
