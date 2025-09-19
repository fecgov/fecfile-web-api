import json
import timeit
from uuid import uuid4
from django.test import TestCase, tag, override_settings
from unittest.mock import patch
from fecfiler.web_services.tasks import (
    calculate_polling_interval,
    create_dot_fec,
    submit_to_fec,
    submit_to_webprint,
    poll_for_fec_response,
    log_polling_notice,
)
from fecfiler.web_services.models import (
    DotFEC,
    FECStatus,
    FECSubmissionState,
    UploadSubmission,
    WebPrintSubmission,
    BaseSubmission,
)
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from pathlib import Path
from fecfiler.settings import CELERY_LOCAL_STORAGE_DIRECTORY
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.contacts.tests.utils import create_test_individual_contact
from fecfiler.transactions.tests.utils import create_schedule_a
from fecfiler.web_services.dot_fec.web_print_submitter import (
    WebPrintSubmitter,
    MockWebPrintSubmitter,
)
from fecfiler.web_services.dot_fec.dot_fec_submitter import MockDotFECSubmitter
from uuid import uuid4 as uuid
from fecfiler.settings import (
    INITIAL_POLLING_MAX_ATTEMPTS,
    SECONDARY_POLLING_MAX_ATTEMPTS,
)

import structlog

logger = structlog.get_logger(__name__)

MAX_ATTEMPTS = INITIAL_POLLING_MAX_ATTEMPTS + SECONDARY_POLLING_MAX_ATTEMPTS


class TasksTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.f3x = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        self.contact_1 = create_test_individual_contact(
            "Smith", "John", self.committee.id
        )

        self.transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2023-01-05",
            "123.45",
            "GENERAL",
            "SA11AI",
            itemized=True,
            report=self.f3x,
        )

    """
    CREATE DOT FEC TESTS
    """

    def test_create_dot_fec(self):
        dot_fec_id = create_dot_fec(str(self.f3x.id), None, None, True)
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

    def test_creating_dot_fec_is_restartable(self):
        dot_fec_record_old = DotFEC.objects.create()
        submission_record_old = WebPrintSubmission.objects.create(
            dot_fec=dot_fec_record_old,
        )
        self.f3x.webprint_submission = submission_record_old
        self.f3x.save()

        new_dot_fec_id = create_dot_fec(
            str(self.f3x.id),
            None,
            submission_record_old.id,
            True
        )

        new_dot_fec_record = DotFEC.objects.get(id=new_dot_fec_id)
        self.assertIsNotNone(new_dot_fec_record)
        self.assertNotEqual(new_dot_fec_id, dot_fec_record_old.id)

    @tag("performance")
    def test_load(self):
        num_a = 2000
        transactions = []

        for _ in range(num_a):
            t = create_schedule_a(
                "INDIVIDUAL_RECEIPT",
                self.committee,
                self.contact_1,
                "2023-01-05",
                "123.45",
                "GENERAL",
                "SA11AI",
                itemized=True,
                report=self.f3x,
            )
            transactions.append(t)

        self.assertEqual(len(transactions), num_a)
        start_time = timeit.default_timer()
        dot_fec_id = create_dot_fec(str(self.f3x.id), None, None, True)
        end_time = timeit.default_timer()
        execution_time = end_time - start_time
        logger.info(f"Execution time: {execution_time:.4f} seconds")
        self.assertIsNotNone(dot_fec_id)

    """
    SUBMIT TO FEC TESTS
    """

    @patch("fecfiler.web_services.tasks.poll_for_fec_response")
    def test_submit_to_fec(self, mock_poll_for_fec_response):
        upload_submission = UploadSubmission.objects.initiate_submission(str(self.f3x.id))
        dot_fec_id = create_dot_fec(
            str(self.f3x.id),
            upload_submission_id=upload_submission.id,
            force_write_to_disk=True,
        )
        submit_to_fec(
            dot_fec_id,
            upload_submission.id,
            "test_password",
            True,
            None,
            True,
        )
        upload_submission.refresh_from_db()
        self.assertEqual(upload_submission.dot_fec_id, dot_fec_id)
        self.assertEqual(
            upload_submission.fecfile_task_state, FECSubmissionState.SUBMITTING.value
        )
        self.assertIsNone(upload_submission.fecfile_error)
        self.assertEqual(upload_submission.fec_submission_id, "fake_submission_id")
        self.assertEqual(upload_submission.fec_status, FECStatus.PROCESSING.value)
        self.assertEqual(
            upload_submission.fec_message, "We didn't really send anything to FEC"
        )
        self.assertEqual(len(upload_submission.fec_report_id), 36)

    def test_submit_no_password(self):
        upload_submission = UploadSubmission.objects.initiate_submission(str(self.f3x.id))
        dot_fec_id = create_dot_fec(
            str(self.f3x.id),
            upload_submission_id=upload_submission.id,
            force_write_to_disk=True,
        )
        submit_to_fec(dot_fec_id, upload_submission.id, None, True, None, True)
        upload_submission.refresh_from_db()
        self.assertEqual(
            upload_submission.fecfile_task_state, FECSubmissionState.FAILED.value
        )
        self.assertEqual(upload_submission.fecfile_error, "No E-Filing Password provided")

    def test_submit_missing_file(self):
        upload_submission = UploadSubmission.objects.initiate_submission(str(self.f3x.id))
        dot_fec_id = create_dot_fec(
            str(self.f3x.id),
            upload_submission_id=upload_submission.id,
            force_write_to_disk=True,
        )
        dot_fec_record = DotFEC.objects.get(id=dot_fec_id)
        path = Path(CELERY_LOCAL_STORAGE_DIRECTORY) / dot_fec_record.file_name
        path.unlink()
        submit_to_fec(dot_fec_id, upload_submission.id, "test_password", True, None, True)
        upload_submission.refresh_from_db()
        self.assertEqual(
            upload_submission.fecfile_task_state, FECSubmissionState.FAILED.value
        )
        self.assertEqual(upload_submission.fecfile_error, "Could not retrieve .FEC bytes")

    """
    SUBMIT TO WEBPRINT TESTS
    """

    def test_submit_to_webprint(self):
        webprint_submission = WebPrintSubmission.objects.initiate_submission(
            str(self.f3x.id)
        )
        dot_fec_id = create_dot_fec(
            str(self.f3x.id),
            webprint_submission_id=webprint_submission.id,
            force_write_to_disk=True,
        )
        webprint_id = submit_to_webprint(dot_fec_id, webprint_submission.id, True, True)
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


class UnitTestWebPrintSubmitter(WebPrintSubmitter):
    # A stand-in WebPrintSubmitter that returns PROCESSING on submission
    # and always returns PROCESSING except on exactly the 4th polling attempt.

    def submit(self, email, dot_fec_bytes):
        """return an accepted message without reaching out to api"""
        return json.dumps(
            {
                "status": FECStatus.PROCESSING.value,
                "image_url": None,
                "message": "Unit Test In Progress",
                "submission_id": str(uuid4()),
                "batch_id": 123,
            }
        )

    def poll_status(self, submission: BaseSubmission):
        submission = WebPrintSubmission.objects.get(id=submission.fec_submission_id)
        status = FECStatus.PROCESSING.value
        if submission.fecfile_polling_attempts == 4:
            status = FECStatus.COMPLETED.value
        return json.dumps(
            {
                "status": status,
                "image_url": "https://www.fec.gov/static/img/seal.svg",
                "message": "This did not really come from FEC",
                "submission_id": submission.fec_submission_id,
                "batch_id": 123,
            }
        )


class UnitTestDotFecSubmitter(MockDotFECSubmitter):
    # A stand-in DotFECSubmitter that returns PROCESSING on submission
    def submit(self, dot_fec_bytes, json_payload, fec_report_id=None):
        return json.dumps(
            {
                "submission_id": "fake_submission_id",
                "status": FECStatus.PROCESSING.value,
                "message": "We didn't really send anything to FEC",
                "report_id": fec_report_id or str(uuid()),
            }
        )


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPOGATES=True)
class PollingTasksTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.f3x = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        self.contact_1 = create_test_individual_contact(
            "Smith", "John", self.committee.id
        )

        self.transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            "2023-01-05",
            "123.45",
            "GENERAL",
            "SA11AI",
            itemized=True,
            report=self.f3x,
        )

        self.mock_web_print_key = "MockWebPrint"
        self.test_print_key = "UnitTestWebPrint"
        self.submission_managers = {
            self.mock_web_print_key: MockWebPrintSubmitter,
            self.test_print_key: UnitTestWebPrintSubmitter,
        }
        self.submission_classes = {
            self.mock_web_print_key: WebPrintSubmission,
            self.test_print_key: WebPrintSubmission,
        }

        self.mock_submitter_key = "MockDotFEC"
        self.test_dot_fec_key = "UnitTestDotFec"
        self.test_dot_fec_submission_managers = {
            self.mock_submitter_key: MockDotFECSubmitter,
            self.test_dot_fec_key: UnitTestDotFecSubmitter,
        }
        self.test_dot_fec_submission_classes = {
            self.mock_submitter_key: UploadSubmission,
            self.test_dot_fec_key: UploadSubmission,
        }

    def test_dotfec_submission_polling_completes(self):
        with patch.multiple(
            "fecfiler.web_services.tasks",
            SUBMISSION_MANAGERS=self.test_dot_fec_submission_managers,
            SUBMISSION_CLASSES=self.test_dot_fec_submission_classes,
        ):
            upload_submission = UploadSubmission.objects.initiate_submission(
                str(self.f3x.id)
            )
            self.assertNotEqual(upload_submission.fec_status, FECStatus.COMPLETED)
            poll_for_fec_response(
                upload_submission.id,
                self.mock_submitter_key,
                "Unit Testing Upload Submission",
            )
            resolved_submission = UploadSubmission.objects.get(id=upload_submission.id)
            self.assertEqual(resolved_submission.fec_status, FECStatus.ACCEPTED)

    def test_submission_polling_completes(self):
        webprint_submission = WebPrintSubmission.objects.initiate_submission(
            str(self.f3x.id)
        )
        self.assertNotEqual(webprint_submission.fec_status, FECStatus.COMPLETED)
        poll_for_fec_response(
            webprint_submission.id, self.mock_web_print_key, "Unit Testing Web Print"
        )
        resolved_submission = WebPrintSubmission.objects.get(id=webprint_submission.id)
        self.assertEqual(resolved_submission.fec_status, FECStatus.COMPLETED)

    def test_submission_ongoing_polling(self):
        with patch.multiple(
            "fecfiler.web_services.tasks",
            SUBMISSION_MANAGERS=self.submission_managers,
            SUBMISSION_CLASSES=self.submission_classes,
        ):
            webprint_submission = WebPrintSubmission.objects.initiate_submission(
                str(self.f3x.id)
            )
            webprint_submission.fec_submission_id = webprint_submission.id
            webprint_submission.save()
            self.assertEqual(webprint_submission.fecfile_polling_attempts, 0)
            poll_for_fec_response(
                webprint_submission.id, self.test_print_key, "Unit Testing Web Print"
            )
            ongoing_submission = WebPrintSubmission.objects.get(id=webprint_submission.id)
            self.assertEqual(ongoing_submission.fec_status, FECStatus.COMPLETED.value)
            self.assertEqual(ongoing_submission.fecfile_polling_attempts, 5)

    def test_submission_polling_limit(self):
        with patch.multiple(
            "fecfiler.web_services.tasks",
            SUBMISSION_MANAGERS=self.submission_managers,
            SUBMISSION_CLASSES=self.submission_classes,
        ):
            webprint_submission = WebPrintSubmission.objects.initiate_submission(
                str(self.f3x.id)
            )
            webprint_submission.fec_submission_id = webprint_submission.id
            webprint_submission.fecfile_polling_attempts = 6
            webprint_submission.save()
            poll_for_fec_response(
                webprint_submission.id, self.test_print_key, "Unit Testing Web Print"
            )
            resolved_submission = WebPrintSubmission.objects.get(
                id=webprint_submission.id
            )
            self.assertEqual(
                resolved_submission.fecfile_task_state, FECSubmissionState.FAILED.value
            )
            self.assertEqual(
                resolved_submission.fecfile_polling_attempts,
                MAX_ATTEMPTS,
            )

    def test_log_polling_notice_does_not_crash(self):
        self.assertIsNone(log_polling_notice(3))

    def test_calculate_polling_interval_throws_exception_when_more_than_max(self):
        with self.assertRaises(ValueError) as context:
            calculate_polling_interval(MAX_ATTEMPTS + 1)

        # Verify the error message
        self.assertEqual(
            str(context.exception), "Polling attempts exceeded the maximum allowed."
        )
