import uuid
from django.db import models
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from .managers import ReportManager
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

    confirmation_email_1 = models.EmailField(
        max_length=44, null=True, blank=True, default=None
    )
    confirmation_email_2 = models.EmailField(
        max_length=44, null=True, blank=True, default=None
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

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

    report_f3x = models.ForeignKey(
        "reports.ReportF3X", on_delete=models.CASCADE, null=True, blank=True
    )

    objects = ReportManager()

    class Meta:
        app_label = "reports"
        db_table = "reports_NEW"


class ReportMixin(models.Model):
    """Abstract model for tracking reports
    """

    report = models.ForeignKey(
        "reports.Report", on_delete=models.CASCADE, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        committee = self.report.committee_account

        if self.report__report_f3x:
            report_date = self.report.report_f3x__coverage_from_date
            if report_date is not None:
                report_year = report_date.year

                reports_to_flag_for_recalculation = Report.objects.filter(
                    ~models.Q(upload_submission__fec_status=models.Value("ACCEPTED")),
                    committee_account=committee,
                    report_f3x__coverage_from_date__year=report_year,
                    report_f3x__coverage_from_date__gte=report_date,
                )
            else:
                reports_to_flag_for_recalculation = [self.report]

            for report in reports_to_flag_for_recalculation:
                report.report_f3x__calculation_status = None
                report.save()
                logger.info(f"F3X Summary: {report.id} marked for recalcuation")

        super(ReportMixin, self).save(*args, **kwargs)

    class Meta:
        abstract = True
