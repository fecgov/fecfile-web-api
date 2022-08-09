from django.db import models


class DotFEC(models.Model):
    """Model storing .FEC file locations

    Look up file names by reports
    """

    report = models.ForeignKey("f3x_summaries.F3XSummary", on_delete=models.CASCADE)
    file_name = models.TextField()

    class Meta:
        db_table = "dot_fecs"


class UploadSubmission(models.Model):
    """Model tracking submissions to FEC Webload"""

    report = models.ForeignKey("f3x_summaries.F3XSummary", on_delete=models.CASCADE)
    """state of internal fecfile submission task"""
    fecfile_task_state = models.CharField(
        choices=(
            ("CREATING_FILE", "CREATING_FILE"),
            ("SUBMITTING", "SUBMITTING"),
            ("SUCCEEDED", "SUCCEEDED"),
            ("FAILED", "FAILED"),
        ),
        max_length=255,
    )
    fec_submission_id = models.CharField(max_length=255)
    fec_status = models.CharField(
        choices=(
            ("ACCEPTED", "ACCEPTED"),
            ("PROCESSING", "PROCESSING"),
            ("REJECTED", "REJECTED"),
        ),
        max_length=255,
    )
    # different from internal report id
    fec_report_id = models.CharField(max_length=255)
    fec_message = models.TextField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "upload_submissions"
