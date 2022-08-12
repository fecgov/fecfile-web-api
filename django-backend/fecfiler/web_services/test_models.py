import json
from django.test import TestCase
from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.web_services.models import (
    FECStatus,
    UploadSubmission,
    FECSubmissionState,
    WebPrintSubmission,
)


class UploadSubmissionTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
    ]

    def setUp(self):
        self.f3x = F3XSummary.objects.filter(id=9999).first()
        self.upload_submission = UploadSubmission()
        self.webprint_submission = WebPrintSubmission()

    """
    WEBLOAD
    """

    def test_initiate_submission(self):
        self.assertIsNone(self.f3x.upload_submission_id)
        submission = UploadSubmission.objects.initiate_submission(9999)
        self.assertEqual(
            submission.fecfile_task_state,
            FECSubmissionState.INITIALIZING.value,
        )
        self.f3x.refresh_from_db()
        self.assertEqual(self.f3x.upload_submission_id, submission.id)

    def test_save_fec_response(self):
        self.assertIsNone(self.upload_submission.fec_status)
        self.upload_submission.save_fec_response(
            json.dumps(
                {
                    "submission_id": "fake_submission_id",
                    "status": FECStatus.ACCEPTED.value,
                    "message": "We didn't really send anything to FEC",
                    "report_id": "1234",
                }
            )
        )
        from_db = UploadSubmission.objects.get(id=self.upload_submission.id)
        self.assertEqual(from_db.fec_submission_id, "fake_submission_id")
        self.assertEqual(from_db.fec_status, "ACCEPTED")
        self.assertEqual(from_db.fec_message, "We didn't really send anything to FEC")
        self.assertEqual(from_db.fec_report_id, "1234")

    def test_save_error(self):
        self.assertIsNone(self.upload_submission.fecfile_error)
        self.upload_submission.save_error("OH NO!")
        from_db = UploadSubmission.objects.get(id=self.upload_submission.id)
        self.assertEqual(from_db.fecfile_error, "OH NO!")
        self.assertEqual(from_db.fecfile_task_state, FECSubmissionState.FAILED.value)

    """
    WEBPRINT
    """

    def test_webprint_initiate_submission(self):
        self.assertIsNone(self.f3x.webprint_submission_id)
        submission = WebPrintSubmission.objects.initiate_submission(9999)
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
                    "message": "We didn't really send anything to FEC",
                    "batch_id": 123,
                }
            )
        )
        from_db = WebPrintSubmission.objects.get(id=self.webprint_submission.id)
        self.assertEqual(from_db.fec_image_url, "google.com")
        self.assertEqual(from_db.fec_submission_id, "fake_submission_id")
        self.assertEqual(from_db.fec_status, "COMPLETED")
        self.assertEqual(from_db.fec_message, "We didn't really send anything to FEC")
        self.assertEqual(from_db.fec_batch_id, "123")
