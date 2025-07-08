from enum import Enum
import json
import uuid
from datetime import datetime, timezone
from django.db import models
from fecfiler.reports.models import Report, ReportMixin
import structlog

logger = structlog.get_logger(__name__)


class DotFEC(ReportMixin):
    """Model storing .FEC file locations

    Look up file names by reports
    """

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    file_name = models.TextField()

    class Meta:
        db_table = "dot_fecs"


class FECSubmissionState(str, Enum):
    """States of submission to FEC
    Can be used for Webload and WebPrint"""

    INITIALIZING = "INITIALIZING"
    CREATING_FILE = "CREATING_FILE"
    SUBMITTING = "SUBMITTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

    def __str__(self):
        return str(self.value)


class FECStatus(str, Enum):
    ACCEPTED = "ACCEPTED"  # Webload
    COMPLETED = "COMPLETED"  # WebPrint
    PROCESSING = "PROCESSING"
    REJECTED = "REJECTED"  # Webload
    FAILED = "FAILED"  # WebPrint

    def __str__(self):
        return str(self.value)

    @classmethod
    def get_terminal_statuses(cls):
        return [
            FECStatus.ACCEPTED,
            FECStatus.COMPLETED,
            FECStatus.FAILED,
            FECStatus.REJECTED,
        ]

    @classmethod
    def get_terminal_statuses_strings(cls):
        return [status.value for status in FECStatus.get_terminal_statuses()]


class UploadSubmissionManager(models.Manager):
    def initiate_submission(self, report_id):
        submission = self.create(fecfile_task_state=FECSubmissionState.INITIALIZING.value)
        submission.save()

        Report.objects.filter(id=report_id).update(
            upload_submission=submission, date_signed=submission.created
        )

        logger.info(
            f"""Submission to Webload has been initialized for report :{report_id}
            (track submission with {submission.id})"""
        )
        return submission


class WebPrintSubmissionManager(models.Manager):
    def initiate_submission(self, report_id):
        submission = self.create(fecfile_task_state=FECSubmissionState.INITIALIZING.value)
        submission.save()

        Report.objects.filter(id=report_id).update(webprint_submission=submission)

        logger.info(
            f"""Submission to WebPrint has been initialized for report :{report_id}
            (track submission with {submission.id})"""
        )
        return submission


class BaseSubmission(models.Model):
    """Base Model tracking submissions to FEC"""

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    dot_fec = models.ForeignKey(DotFEC, on_delete=models.SET_NULL, null=True)
    """state of internal fecfile submission task"""
    fecfile_task_state = models.CharField(max_length=255)
    fecfile_error = models.TextField(null=True)
    fecfile_polling_attempts = models.IntegerField(default=0)

    """FEC response fields"""
    fec_submission_id = models.CharField(max_length=255, null=True)
    fec_status = models.CharField(max_length=255, null=True)
    fec_message = models.TextField(null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    task_completed = models.DateTimeField(null=True)

    def save_fec_response(self, response_string):
        logger.debug(f"FEC response: {response_string}")
        fec_response_json = json.loads(response_string)
        self.fec_submission_id = fec_response_json.get("submission_id")
        self.fec_status = fec_response_json.get("status")
        self.fec_message = fec_response_json.get("message")
        self.save()

    def save_error(self, error):
        self.fecfile_task_state = FECSubmissionState.FAILED
        self.fecfile_error = error
        logger.error(f"Submission {self.id} FAILED {self.fecfile_error}")
        self.mark_task_completed()
        self.save()

    def save_state(self, new_state):
        self.fecfile_task_state = new_state
        logger.info(f"Submission {self.id} is {self.fecfile_task_state}")
        if new_state == FECSubmissionState.SUCCEEDED:
            self.mark_task_completed()

        self.save()

    def mark_task_completed(self):
        self.task_completed = datetime.now(timezone.utc)
        if self.created is not None:
            logger.info(f"task completed in {self.task_completed - self.created}")
        else:
            logger.warning("task completed but no created timestamp")

    def log_submission_failure_state(self):
        file_name = None
        report_id = None
        committee_uuid = None
        if self.dot_fec is not None:
            file_name = self.dot_fec.file_name
            if self.dot_fec.report is not None:
                report_id = str(self.dot_fec.report.id)
                if self.dot_fec.report.committee_account is not None:
                    committee_uuid = str(self.dot_fec.report.committee_account.id)

        submission_state = {"efo_submission_failure": {
            "submission_id": str(self.id),
            "report_id": report_id,
            "committee_uuid": committee_uuid,
            "dot_fec_filename": file_name,
            "fecfile_task_state": self.fecfile_task_state,
            "fecfile_polling_attempts": self.fecfile_polling_attempts,
            "fecfile_error": self.fecfile_error,
            "fec_submission_id": self.fec_submission_id,
            "fec_status": self.fec_status,
            "fec_message": self.fec_message,
            "task_completed": str(self.task_completed)
        }}

        logger.warning(json.dumps(submission_state))

    class Meta:
        abstract = True


class UploadSubmission(BaseSubmission):
    """Model tracking submissions to FEC Webload"""

    # different from internal report id
    fec_report_id = models.CharField(max_length=255, null=True)

    objects = UploadSubmissionManager()

    def save_fec_response(self, response_string):
        try:
            fec_response_json = json.loads(response_string)
        except Exception as error:
            logger.error("Failed to parse JSON response from upload submission")
            raise error

        self.fec_report_id = fec_response_json.get("report_id")
        report = self.report_set.first()
        if not report.report_id:
            report.report_id = self.fec_report_id
        report.save()
        super().save_fec_response(response_string)

    class Meta:
        db_table = "upload_submissions"


class WebPrintSubmission(BaseSubmission):
    """Model tracking submissions to FEC WebPrint"""

    fec_image_url = models.CharField(max_length=255, null=True)
    fec_batch_id = models.CharField(max_length=255, null=True)
    fec_email = models.CharField(max_length=255, null=True)

    objects = WebPrintSubmissionManager()

    def save_fec_response(self, response_string):
        try:
            fec_response_json = json.loads(response_string)
        except Exception as error:
            logger.error("Failed to parse JSON response from web print submission")
            raise error

        self.fec_image_url = fec_response_json.get("image_url")
        self.fec_batch_id = fec_response_json.get("batch_id")
        self.fec_email = fec_response_json.get("email")
        return super().save_fec_response(response_string)

    class Meta:
        db_table = "webprint_submissions"
