from enum import Enum
import json
import uuid
from django.db import models
from fecfiler.reports.f3x_report.models import F3XReport
import logging

logger = logging.getLogger(__name__)


class DotFEC(models.Model):
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
    report = models.ForeignKey(F3XReport, on_delete=models.CASCADE)
    file_name = models.TextField()

    class Meta:
        db_table = "dot_fecs"


class FECSubmissionState(Enum):
    """States of submission to FEC
    Can be used for Webload and WebPrint"""

    INITIALIZING = "INITIALIZING"
    CREATING_FILE = "CREATING_FILE"
    SUBMITTING = "SUBMITTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

    def __str__(self):
        return str(self.value)


class FECStatus(Enum):
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
        submission = self.create(
            fecfile_task_state=FECSubmissionState.INITIALIZING.value
        )
        submission.save()

        F3XReport.objects.filter(id=report_id).update(upload_submission=submission)

        logger.info(
            f"""Submission to Webload has been initialized for report :{report_id}
            (track submission with {submission.id})"""
        )
        return submission


class WebPrintSubmissionManager(models.Manager):
    def initiate_submission(self, report_id):
        submission = self.create(
            fecfile_task_state=FECSubmissionState.INITIALIZING.value
        )
        submission.save()

        F3XReport.objects.filter(id=report_id).update(webprint_submission=submission)

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

    """FEC response fields"""
    fec_submission_id = models.CharField(max_length=255, null=True)
    fec_status = models.CharField(max_length=255, null=True)
    fec_message = models.TextField(null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

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
        self.save()

    def save_state(self, new_state):
        self.fecfile_task_state = new_state
        logger.info(f"Submission {self.id} is {self.fecfile_task_state}")
        self.save()

    class Meta:
        abstract = True


class UploadSubmission(BaseSubmission):
    """Model tracking submissions to FEC Webload"""

    # different from internal report id
    fec_report_id = models.CharField(max_length=255, null=True)

    objects = UploadSubmissionManager()

    def save_fec_response(self, response_string):
        fec_response_json = json.loads(response_string)
        self.fec_report_id = fec_response_json.get("report_id")
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
        fec_response_json = json.loads(response_string)
        self.fec_image_url = fec_response_json.get("image_url")
        self.fec_batch_id = fec_response_json.get("batch_id")
        self.fec_email = fec_response_json.get("email")
        return super().save_fec_response(response_string)

    class Meta:
        db_table = "webprint_submissions"
