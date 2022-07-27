from django.db import models


class DotFEC(models.Model):
    """Model storing .FEC file locations

    Look up file names by reports
    """

    report = models.ForeignKey("f3x_summaries.F3XSummary", on_delete=models.CASCADE)
    file_name = models.TextField()

    class Meta:
        db_table = "dot_fecs"
