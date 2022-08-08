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
    submission_id = models.CharField(max_length=255)
    api = models.CharField(max_length=255)
    status = models.CharField(
        choices=(
            ("ACCEPTED", "ACCEPTED"),
            ("PROCESSING", "PROCESSING"),
            ("REJECTED", "REJECTED"),
        ),
        max_length=255,
    )
    # different from internal report id
    fec_report_id = models.CharField(max_length=255)
    message = models.TextField()

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "upload_submissions"
