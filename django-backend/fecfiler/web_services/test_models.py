import json
from django.test import TestCase
from fecfiler.web_services.models import (
    FECStatus,
    UploadSubmission,
    FECSubmissionState,
    WebPrintSubmission,
)
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.views import create_committee_view
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.user.models import User


class UploadSubmissionTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.user = User.objects.create(email="test@fec.gov", username="gov")
        create_committee_view(self.committee.id)
        self.f3x = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        self.upload_submission = UploadSubmission()
        self.webprint_submission = WebPrintSubmission()

    """
    WEBLOAD
    """

    def test_initiate_submission(self):
        self.assertIsNone(self.f3x.upload_submission_id)
        submission = UploadSubmission.objects.initiate_submission(str(self.f3x.id))
        self.assertEqual(
            submission.fecfile_task_state,
            FECSubmissionState.INITIALIZING.value,
        )
        self.assertIsNone(submission.task_completed)
        self.f3x.refresh_from_db()
        self.assertEqual(self.f3x.upload_submission_id, submission.id)

        submission.refresh_from_db()
        self.assertIsNone(submission.fec_status)
        submission.save_fec_response(
            json.dumps(
                {
                    "submission_id": "fake_submission_id",
                    "status": FECStatus.ACCEPTED.value,
                    "message": "Test Save Response",
                    "report_id": "1234",
                }
            )
        )
        from_db = UploadSubmission.objects.get(id=submission.id)
        self.assertEqual(from_db.fec_submission_id, "fake_submission_id")
        self.assertEqual(from_db.fec_status, "ACCEPTED")
        self.assertEqual(from_db.fec_message, "Test Save Response")
        self.assertEqual(from_db.fec_report_id, "1234")
        self.assertIsNone(from_db.task_completed)
        from_db.save_state(FECSubmissionState.SUCCEEDED)
        self.assertIsNotNone(from_db.task_completed)

    def test_save_error(self):
        self.assertIsNone(self.upload_submission.fecfile_error)
        self.upload_submission.save_error("OH NO!")
        from_db = UploadSubmission.objects.get(id=self.upload_submission.id)
        self.assertEqual(from_db.fecfile_error, "OH NO!")
        self.assertEqual(from_db.fecfile_task_state, FECSubmissionState.FAILED.value)
        self.assertIsNotNone(from_db.task_completed)

    """
    WEBPRINT
    """

    def test_webprint_initiate_submission(self):
        self.assertIsNone(self.f3x.webprint_submission_id)
        submission = WebPrintSubmission.objects.initiate_submission(str(self.f3x.id))
        self.assertEqual(
            submission.fecfile_task_state,
            FECSubmissionState.INITIALIZING.value,
        )
        self.f3x.refresh_from_db()
        self.assertEqual(self.f3x.webprint_submission_id, submission.id)

    def test_webprint_save_fec_response(self):
        self.assertIsNone(self.webprint_submission.fec_status)
        self.webprint_submission.save_fec_response(
            json.dumps(
                {
                    "image_url": "google.com",
                    "submission_id": "fake_submission_id",
                    "status": FECStatus.COMPLETED.value,
                    "message": "Test Webprint Response",
                    "batch_id": 123,
                }
            )
        )
        from_db = WebPrintSubmission.objects.get(id=self.webprint_submission.id)
        self.assertEqual(from_db.fec_image_url, "google.com")
        self.assertEqual(from_db.fec_submission_id, "fake_submission_id")
        self.assertEqual(from_db.fec_status, "COMPLETED")
        self.assertEqual(from_db.fec_message, "Test Webprint Response")
        self.assertEqual(from_db.fec_batch_id, "123")
