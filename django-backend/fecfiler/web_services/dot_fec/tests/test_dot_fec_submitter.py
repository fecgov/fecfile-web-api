import json
from uuid import uuid4 as uuid
from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_submitter import MockDotFECSubmitter
from fecfiler.web_services.dot_fec.web_print_submitter import MockWebPrintSubmitter
from fecfiler.web_services.models import DotFEC
from fecfiler.web_services.tasks import create_dot_fec
from fecfiler.committee_accounts.views import create_committee_view
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x


class DotFECSubmitterTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
        self.f3x = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        self.dot_fec_id = create_dot_fec(
            str(self.f3x.id),
            force_write_to_disk=True,
        )
        self.dot_fec_record = DotFEC.objects.get(id=self.dot_fec_id)

    def test_get_submission_json(self):
        submitter = MockDotFECSubmitter()
        json_str = submitter.get_submission_json(
            self.dot_fec_record, "test_json_password"
        )
        json_obj = json.loads(json_str)
        self.assertEqual(json_obj["email_1"], self.f3x.confirmation_email_1)
        self.assertEqual(json_obj["email_2"], self.f3x.confirmation_email_2)
        self.assertFalse(json_obj["wait"])

    def test_get_submission_json_for_amendment(self):
        submitter = MockDotFECSubmitter()
        self.dot_fec_record.report.report_id = str(uuid())
        json_str = submitter.get_submission_json(
            self.dot_fec_record, "test_json_password", "test_backdoor_code"
        )
        json_obj = json.loads(json_str)
        self.assertEqual(
            json_obj["amendment_id"],
            self.dot_fec_record.report.report_id + "test_backdoor_code",
        )

    def test_poll(self):
        submitter = MockDotFECSubmitter()
        response = submitter.poll_status(self.dot_fec_record.id)
        response_obj = json.loads(response)
        self.assertEqual(response_obj["status"], "ACCEPTED")

        submitter = MockWebPrintSubmitter()
        response = submitter.poll_status(123, str(uuid()))
        response_obj = json.loads(response)
        self.assertEqual(response_obj["status"], "COMPLETED")
