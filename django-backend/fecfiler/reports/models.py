import uuid
from django.db import models, transaction as db_transaction
from django.db.models import Q
from decimal import Decimal
import copy
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
        "reports.reportf3x", on_delete=models.CASCADE, null=True, blank=True
    )
    report_f24 = models.ForeignKey(
        "reports.reportf24", on_delete=models.CASCADE, null=True, blank=True
    )
    report_f99 = models.ForeignKey(
        "reports.reportf99", on_delete=models.CASCADE, null=True, blank=True
    )

    objects = ReportManager()

    def save(self, *args, **kwargs):
        # Record if the is a create or update operation
        create_action = self.created is None

        with db_transaction.atomic():
            super(Report, self).save(*args, **kwargs)

            # Pull forward any loans with non-zero balances along with their
            # loan guarantors
            if create_action and self.coverage_through_date:
                self.pull_forward_loans()
                self.pull_forward_debts()

    def pull_forward_loans(self):
        previous_report = self.get_previous_report()

        if previous_report:
            loans_to_pull_forward = previous_report.transaction_set.filter(
                ~Q(loan_balance=Decimal(0)) | Q(loan_balance__isnull=True),
                ~Q(memo_code=True),
                schedule_c_id__isnull=False,
            )

            for loan in loans_to_pull_forward:
                # Save children as they are lost from the loan object
                # when the loan is saved
                loan_children = copy.deepcopy(loan.children)

                loan.schedule_c_id = self.save_copy(loan.schedule_c)
                loan.memo_text_id = self.save_copy(loan.memo_text)
                loan.report_id = self.id
                loan.report = self
                # The loan_id should point to the original loan transaction
                # even if the loan is pulled forward multiple times.
                loan.loan_id = loan.loan_id if loan.loan_id else loan.id
                self.save_copy(loan)
                for child in loan_children:
                    # If child is a guarantor transaction, copy it
                    # and link it to the new loan
                    if child.schedule_c2_id:
                        child.schedule_c2_id = self.save_copy(child.schedule_c2)
                        child.memo_text_id = self.save_copy(child.memo_text)
                        child.report_id = self.id
                        child.report = self
                        child.parent_transaction_id = loan.id
                        child.parent_transaction = loan
                        self.save_copy(child)

    def pull_forward_debts(self):
        previous_report = self.get_previous_report()

        if previous_report:
            debts_to_pull_forward = previous_report.transaction_set.filter(
                ~Q(balance_at_close=Decimal(0)) | Q(balance_at_close__isnull=True),
                ~Q(memo_code=True),
                schedule_d_id__isnull=False,
            )

            for debt in debts_to_pull_forward:
                debt.schedule_d.incurred_amount = Decimal(0)
                debt.schedule_d_id = self.save_copy(debt.schedule_d)
                debt.report_id = self.id
                debt.report = self
                # The debt_id should point to the original debt transaction
                # even if the debt is pulled forward multiple times.
                debt.debt_id = debt.debt_id if debt.debt_id else debt.id
                self.save_copy(debt)

    def get_previous_report(self):
        return (
            Report.objects.get_queryset()
            .filter(
                committee_account=self.committee_account,
                coverage_through_date__lt=self.coverage_through_date,
            )
            .order_by("coverage_through_date")
            .last()
        )

    def save_copy(self, fkey):
        if fkey:
            fkey.pk = fkey.id = None
            fkey._state.adding = True
            fkey.save()
            return fkey.id
        return None


class ReportMixin(models.Model):
    """Abstract model for tracking reports"""

    report = models.ForeignKey(
        "reports.Report", on_delete=models.CASCADE, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if self.report:
            committee = self.report.committee_account
            report_date = self.report.coverage_from_date
            if report_date is not None:
                report_year = report_date.year

                reports_to_flag_for_recalculation = Report.objects.filter(
                    ~models.Q(upload_submission__fec_status=models.Value("ACCEPTED")),
                    committee_account=committee,
                    coverage_from_date__year=report_year,
                    coverage_from_date__gte=report_date,
                )
            else:
                reports_to_flag_for_recalculation = [self.report]

            for report in reports_to_flag_for_recalculation:
                report.calculation_status = None
                report.save()
                logger.info(f"Report: {report.id} marked for recalcuation")

        super(ReportMixin, self).save(*args, **kwargs)

    class Meta:
        abstract = True
