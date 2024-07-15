import datetime
import timeit
from django.test import TestCase, tag
from .tasks import create_dot_fec, submit_to_fec, submit_to_webprint
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
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.views import create_committee_view
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.contacts.tests.utils import create_test_individual_contact
from fecfiler.transactions.tests.utils import create_schedule_a
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.models import Transaction
from fecfiler.reports.models import ReportTransaction

import structlog

logger = structlog.get_logger(__name__)


class TasksTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
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

    def test_submit_to_fec(self):
        upload_submission = UploadSubmission.objects.initiate_submission(str(self.f3x.id))
        dot_fec_id = create_dot_fec(
            str(self.f3x.id),
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
        upload_submission = UploadSubmission.objects.initiate_submission(str(self.f3x.id))
        dot_fec_id = create_dot_fec(
            str(self.f3x.id),
            upload_submission_id=upload_submission.id,
            force_write_to_disk=True,
        )
        submit_to_fec(dot_fec_id, upload_submission.id, None, None, True)
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
        submit_to_fec(dot_fec_id, upload_submission.id, "test_password", None, True)
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


from django.db import connection


def bulk_insert(values):
    base_sql = "INSERT INTO transactions_transaction (transaction_type_identifier, aggregration_group, _form_type) VALUES"
    values_sql = []
    values_data = []

    for value_list in values:
        placeholders = ["%s" for _ in range(len(value_list))]
        values_sql.append(f"({', '.join(placeholders)})")
        values_data.extend(value_list)

    sql = f"{base_sql} {', '.join(values_sql)}"
    with connection.cursor() as cursor:
        cursor.executemany(sql, [values_data])
