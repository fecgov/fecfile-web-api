import base64
from django.test import TestCase
from .tasks import create_dot_fec, get_dot_fec, submit_to_fec, submit_to_webprint
from fecfiler.reports.models import Report
from fecfiler.transactions.models import Transaction
from .models import (
    DotFEC,
    FECStatus,
    FECSubmissionState,
    UploadSubmission,
    WebPrintSubmission,
)
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from pathlib import Path
from fecfiler.settings import CELERY_LOCAL_STORAGE_DIRECTORY
from fecfiler.committee_accounts.views import create_committee_view


class TasksTestCase(TestCase):
    fixtures = [
        "C01234567_user_and_committee",
        "test_f3x_reports",
        "test_individual_receipt",
        "test_memo_text",
    ]

    def setUp(self):
        create_committee_view("11111111-2222-3333-4444-555555555555")
        self.f3x = Report.objects.filter(
            id="b6d60d2d-d926-4e89-ad4b-c47d152a66ae"
        ).first()
        self.transaction = Transaction.objects.filter(
            id="e7880981-9ee7-486f-b288-7a607e4cd0dd"
        ).first()

    """
    CREATE DOT FEC TESTS
    """

    def test_create_dot_fec(self):
        dot_fec_id = create_dot_fec(
            "b6d60d2d-d926-4e89-ad4b-c47d152a66ae", None, None, True
        )
        dot_fec_record = DotFEC.objects.get(id=dot_fec_id)
        result_dot_fec = Path(CELERY_LOCAL_STORAGE_DIRECTORY).joinpath(
            dot_fec_record.file_name
        )
        try:
            with open(result_dot_fec, encoding="utf-8") as f:
                lines = f.readlines()
                self.assertEqual(lines[0][:4], "HDR" + FS_STR)
                self.assertEqual(lines[1][:5], "F3XN" + FS_STR)
                self.assertEqual(lines[2][:7], "SA11AI" + FS_STR)
        finally:
            if result_dot_fec.exists():
                result_dot_fec.unlink()

    """
    SUBMIT TO FEC TESTS
    """

    def test_submit_to_fec(self):
        upload_submission = UploadSubmission.objects.initiate_submission(
            "b6d60d2d-d926-4e89-ad4b-c47d152a66ae"
        )
        dot_fec_id = create_dot_fec(
            "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            upload_submission_id=upload_submission.id,
            force_write_to_disk=True,
        )
        upload_id = submit_to_fec(
            dot_fec_id,
            upload_submission.id,
            "test_password",
            None,
            True,
        )
        upload_submission.refresh_from_db()
        self.assertEqual(upload_id, upload_submission.id)
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
        upload_submission = UploadSubmission.objects.initiate_submission(
            "b6d60d2d-d926-4e89-ad4b-c47d152a66ae"
        )
        dot_fec_id = create_dot_fec(
            "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
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
        upload_submission = UploadSubmission.objects.initiate_submission(
            "b6d60d2d-d926-4e89-ad4b-c47d152a66ae"
        )
        dot_fec_id = create_dot_fec(
            "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
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
        webprint_submission = WebPrintSubmission.objects.initiate_submission(
            "b6d60d2d-d926-4e89-ad4b-c47d152a66ae"
        )
        dot_fec_id = create_dot_fec(
            "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            webprint_submission_id=webprint_submission.id,
            force_write_to_disk=True,
        )
        webprint_id = submit_to_webprint(dot_fec_id, webprint_submission.id, None, True)
        webprint_submission.refresh_from_db()
        self.assertEqual(webprint_id, webprint_submission.id)
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

    def test_get_dot_fec(self):
        dot_fec_id = create_dot_fec(
            "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            force_write_to_disk=True,
        )
        dot_fec_record = DotFEC.objects.filter(id=dot_fec_id).first()
        file_name = dot_fec_record.file_name
        file_content_base64 = get_dot_fec(file_name)
        file_content_bytes = base64.b64decode(file_content_base64)
        content_string = file_content_bytes.decode("utf-8")
        self.assertIn("F3XN", content_string)
