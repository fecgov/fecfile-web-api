import uuid
from django.db import models
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from .managers import ReportManager
from fecfiler.reports.report_f3x.models import ReportF3X
import logging


logger = logging.getLogger(__name__)


class Report(SoftDeleteModel, CommitteeOwnedModel):
    """Generated model from json schema"""

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    form_type = models.TextField(null=True, blank=True)

    upload_submission = models.ForeignKey(
        "web_services.UploadSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    webprint_submission = models.ForeignKey(
        "web_services.WebPrintSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    report_f3x = models.ForeignKey(
        ReportF3X, on_delete=models.CASCADE, null=True, blank=True
    )

    objects = ReportManager()

    class Meta:
        db_table = "reports"


class ReportMixin(models.Model):
    """Abstract model for tracking reports
    """

    report = models.ForeignKey(
        "reports.Report", on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        abstract = True
