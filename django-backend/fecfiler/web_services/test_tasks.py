from django.test import TestCase
from .tasks import create_dot_fec, submit_to_fec, submit_to_webprint
from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.scha_transactions.models import SchATransaction
from .models import (
    DotFEC,
    FECStatus,
    FECSubmissionState,
    UploadSubmission,
    WebPrintSubmission,
)
from curses import ascii
from pathlib import Path
from fecfiler.settings import CELERY_LOCAL_STORAGE_DIRECTORY


class TasksTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_individual_receipt",
    ]

    def setUp(self):
        self.f3x = F3XSummary.objects.filter(id=9999).first()
        self.transaction = SchATransaction.objects.filter(id=9999).first()

    """
    CREATE DOT FEC TESTS
    """

    def test_create_dot_fec(self):
        dot_fec_id = create_dot_fec(9999, None, None, True)
        dot_fec_record = DotFEC.objects.get(id=dot_fec_id)
        result_dot_fec = Path(CELERY_LOCAL_STORAGE_DIRECTORY).joinpath(
            dot_fec_record.file_name
        )
        try:
            with open(result_dot_fec, encoding="utf-8") as f:
                lines = f.readlines()
                self.assertEqual(lines[0][:4], "HDR" + chr(ascii.FS))
                self.assertEqual(lines[1][:5], "F3XN" + chr(ascii.FS))
                self.assertEqual(lines[2][:7], "SA11AI" + chr(ascii.FS))
        finally:
            if result_dot_fec.exists():
                result_dot_fec.unlink()

    """
    SUBMIT TO FEC TESTS
    """

    def test_submit_to_fec(self):
        upload_submission = UploadSubmission.objects.initiate_submission(9999)
        dot_fec_id = create_dot_fec(
            9999,
            upload_submission_id=upload_submission.id,
            force_write_to_disk=True,
        )
        id = submit_to_fec(
            dot_fec_id,
            upload_submission.id,
            "test_password",
            None,
            True,
        )
        upload_submission.refresh_from_db()
        self.assertEqual(id, upload_submission.id)
        self.assertEqual(upload_submission.dot_fec_id, dot_fec_id)
        self.assertEqual(
            upload_submission.fecfile_task_state, FECSubmissionState.SUCCEEDED.value
        )
        self.assertIsNone(upload_submission.fecfile_error)
        self.assertEqual(upload_submission.fec_submission_id, "fake_submission_id")
        self.assertEqual(upload_submission.fec_status, FECStatus.ACCEPTED.value)
        self.assertEqual(
            upload_submission.fec_message, "We didn't really send anything to FEC"
        )
        self.assertEqual(len(upload_submission.fec_report_id), 36)

    def test_submit_no_password(self):
        upload_submission = UploadSubmission.objects.initiate_submission(9999)
        dot_fec_id = create_dot_fec(
            9999,
            upload_submission_id=upload_submission.id,
            force_write_to_disk=True,
        )
        submit_to_fec(dot_fec_id, upload_submission.id, None, None, True)
        upload_submission.refresh_from_db()
        self.assertEqual(
            upload_submission.fecfile_task_state, FECSubmissionState.FAILED.value
        )
        self.assertEqual(
            upload_submission.fecfile_error, "No E-Filing Password provided"
        )

    def test_submit_missing_file(self):
        upload_submission = UploadSubmission.objects.initiate_submission(9999)
        dot_fec_id = create_dot_fec(
            9999,
            upload_submission_id=upload_submission.id,
            force_write_to_disk=True,
        )
        dot_fec_record = DotFEC.objects.get(id=dot_fec_id)
        path = Path(CELERY_LOCAL_STORAGE_DIRECTORY) / dot_fec_record.file_name
        path.unlink()
        submit_to_fec(dot_fec_id, upload_submission.id, "test_password", None, True)
        upload_submission.refresh_from_db()
        self.assertEqual(
            upload_submission.fecfile_task_state, FECSubmissionState.FAILED.value
        )
        self.assertEqual(
            upload_submission.fecfile_error, "Could not retrieve .FEC bytes"
        )

    """
    SUBMIT TO WEBPRINT TESTS
    """

    def test_submit_to_webprint(self):
        webprint_submission = WebPrintSubmission.objects.initiate_submission(9999)
        dot_fec_id = create_dot_fec(
            9999,
            webprint_submission_id=webprint_submission.id,
            force_write_to_disk=True,
        )
        id = submit_to_webprint(dot_fec_id, webprint_submission.id, None, True)
        webprint_submission.refresh_from_db()
        self.assertEqual(id, webprint_submission.id)
        self.assertEqual(webprint_submission.dot_fec_id, dot_fec_id)
        self.assertEqual(
            webprint_submission.fecfile_task_state, FECSubmissionState.SUCCEEDED.value
        )
        self.assertIsNone(webprint_submission.fecfile_error)
        self.assertEqual(len(webprint_submission.fec_submission_id), 36)
        self.assertEqual(webprint_submission.fec_status, FECStatus.COMPLETED.value)
        self.assertEqual(
            webprint_submission.fec_message, "This did not really come from FEC"
        )
        self.assertEqual(
            webprint_submission.fec_image_url, "https://www.fec.gov/static/img/seal.svg"
        )
