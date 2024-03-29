import uuid
from django.db import models, transaction as db_transaction
from django.db.models import Q
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from .managers import ReportManager
from .form_3x.models import Form3X
from .form_24.models import Form24
from .form_99.models import Form99
from .form_1m.models import Form1M
import structlog

logger = structlog.get_logger(__name__)


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
    report_version = models.TextField(
        null=True, blank=True
    )  # fec 1-up version of amendment
    report_id = models.TextField(null=True, blank=True)  # fec id for report
    report_code = models.TextField(null=True, blank=True)
    coverage_from_date = models.DateField(null=True, blank=True)
    coverage_through_date = models.DateField(null=True, blank=True)
    treasurer_last_name = models.TextField(null=True, blank=True)
    treasurer_first_name = models.TextField(null=True, blank=True)
    treasurer_middle_name = models.TextField(null=True, blank=True)
    treasurer_prefix = models.TextField(null=True, blank=True)
    treasurer_suffix = models.TextField(null=True, blank=True)
    date_signed = models.DateField(null=True, blank=True)
    calculation_status = models.CharField(max_length=255, null=True, blank=True)
    calculation_token = models.UUIDField(  # Prevents race conditions in summary calc.
        null=True, blank=True, default=None
    )

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

    form_3x = models.ForeignKey(Form3X, on_delete=models.CASCADE, null=True, blank=True)
    form_24 = models.ForeignKey(Form24, on_delete=models.CASCADE, null=True, blank=True)
    form_99 = models.ForeignKey(Form99, on_delete=models.CASCADE, null=True, blank=True)
    form_1m = models.ForeignKey(Form1M, on_delete=models.CASCADE, null=True, blank=True)

    objects = ReportManager()

    @property
    def previous_report(self):
        return (
            Report.objects.get_queryset()
            .filter(
                committee_account=self.committee_account,
                coverage_through_date__lt=self.coverage_from_date,
            )
            .order_by("coverage_through_date")
            .last()
        )

    def save(self, *args, **kwargs):
        from fecfiler.transactions.schedule_c.utils import carry_forward_loans
        from fecfiler.transactions.schedule_d.utils import carry_forward_debts

        # Record if the is a create or update operation
        create_action = self.created is None

        with db_transaction.atomic():
            super(Report, self).save(*args, **kwargs)

            # Pull forward any loans with non-zero balances along with their
            # loan guarantors
            if create_action and self.coverage_through_date:
                carry_forward_loans(self)
                carry_forward_debts(self)
                update_recalculation(self)

    def get_future_in_progress_reports(
        self,
    ):
        return Report.objects.get_queryset().filter(
            ~Q(id=self.id),
            committee_account=self.committee_account_id,
            upload_submission__isnull=True,
            coverage_through_date__gte=self.coverage_through_date,
        )

    def get_form_name(self):
        for form_key in TABLE_TO_FORM:
            if getattr(self, form_key, None):
                return TABLE_TO_FORM.get(form_key)

    def amend(self):
        self.form_type = self.get_form_name() + "A"
        self.report_version = int(self.report_version or "0") + 1

        if self.form_type == "F24A" and self.upload_submission is not None:
            self.form_24.original_amendment_date = self.upload_submission.created
            self.form_24.save()

        self.upload_submission = None
        self.save()


TABLE_TO_FORM = {
    "form_3x": "F3X",
    "form_24": "F24",
    "form_99": "F99",
    "form_1m": "F1M",
}


def update_recalculation(report: Report):
    if report:
        committee = report.committee_account
        report_date = report.coverage_from_date
        if report_date is not None:
            reports_to_flag_for_recalculation = Report.objects.filter(
                committee_account=committee,
                coverage_from_date__gte=report_date,
            )
        else:
            reports_to_flag_for_recalculation = [report]

        for report_to_recalc in reports_to_flag_for_recalculation:
            report_to_recalc.calculation_status = None
            report_to_recalc.save()
            logger.info(f"Report: {report_to_recalc.id} marked for recalcuation")


class ReportMixin(models.Model):
    """Abstract model for tracking reports"""

    report = models.ForeignKey(
        "reports.Report", on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        abstract = True


class ReportTransaction(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    transaction = models.ForeignKey(
        "transactions.Transaction", on_delete=models.CASCADE
    )
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
