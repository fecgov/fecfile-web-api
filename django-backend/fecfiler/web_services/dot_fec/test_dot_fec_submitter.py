import json
from django.test import TestCase
from .dot_fec_submitter import DotFECSubmitter
from fecfiler.web_services.models import DotFEC
from fecfiler.web_services.tasks import create_dot_fec
from fecfiler.reports.models import Report


class DotFECSubmitterTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_reports",
    ]

    def setUp(self):
        self.f3x = Report.objects.filter(
            id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae"
        ).first()
        self.dot_fec_id = create_dot_fec(
            "b6d60d2d-d926-4e89-ad4b-c47d152a66ae", force_write_to_disk=True,
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
