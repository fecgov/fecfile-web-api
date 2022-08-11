from enum import Enum
import json
from django.db import models
import logging

logger = logging.getLogger(__name__)


class DotFEC(models.Model):
    """Model storing .FEC file locations

    Look up file names by reports
    """

    report = models.ForeignKey("f3x_summaries.F3XSummary", on_delete=models.CASCADE)
    file_name = models.TextField()

    class Meta:
        db_table = "dot_fecs"


class UploadSubmissionState(Enum):
    """States of upload submission"""

    INITIALIZING = "INITIALIZING"
    CREATING_FILE = "CREATING_FILE"
    SUBMITTING = "SUBMITTING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


class FECStatus(Enum):
    ACCEPTED = "ACCEPTED"
    PROCESSING = "PROCESSING"
    REJECTED = "REJECTED"


class UploadSubmissionManager(models.Manager):
    def initiate_submission(self, report_id):
        submission = self.create(
            report_id=report_id, fecfile_task_state=UploadSubmissionState.INITIALIZING
        )
        submission.save()

        logger.info(
            f"Submission to Webload has been initialized for report :{report_id} (track submission with {submission.id})"
        )
        return submission


class UploadSubmission(models.Model):
    """Model tracking submissions to FEC Webload"""

    report = models.ForeignKey("f3x_summaries.F3XSummary", on_delete=models.CASCADE)
    dot_fec = models.ForeignKey("web_services.DotFEC", on_delete=models.DO_NOTHING)
    """state of internal fecfile submission task"""
    fecfile_task_state = models.CharField(max_length=255)
    fecfile_error = models.TextField()

    fec_submission_id = models.CharField(max_length=255)
    fec_status = models.CharField(max_length=255)
    # different from internal report id
    fec_report_id = models.CharField(max_length=255)
    fec_message = models.TextField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = UploadSubmissionManager()

    def save_fec_response(self, response_string):
        logger.debug(f"FEC upload response: {response_string}")
        fec_response_json = json.loads(response_string)
        self.fec_submission_id = fec_response_json["submission_id"]
        self.fec_status = fec_response_json["status"]
        self.fec_message = fec_response_json["message"]
        self.fec_report_id = fec_response_json["report_id"]

        self.save()

    def save_error(self, error):
        self.fecfile_task_state = UploadSubmissionState.FAILED
        self.fecfile_error = error
        logger.error(f"Submission for report {self.report_id} FAILED {self.error}")
        self.save()

    def save_state(self, new_state):
        self.fecfile_task_state = new_state
        logger.info(
            f"Submission for report {self.report_id} is {self.fecfile_task_state}"
        )
        self.save()

    class Meta:
        db_table = "upload_submissions"
