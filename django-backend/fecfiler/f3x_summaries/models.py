import uuid
from django.db import models
from django.db import transaction as db_transaction
from django.db.models import Q
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel
from decimal import Decimal
import logging
import copy


logger = logging.getLogger(__name__)


class F3XSummary(SoftDeleteModel, CommitteeOwnedModel):
    """Generated model from json schema"""

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    form_type = models.TextField(null=True, blank=True)
    # TODO get rid of this field.  It is redundant with the related Committee_Account
    committee_name = models.TextField(null=True, blank=True)
    change_of_address = models.BooleanField(default=False, null=True, blank=True)
    street_1 = models.TextField(null=True, blank=True)
    street_2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    confirmation_email_1 = models.EmailField(
        max_length=44, null=True, blank=True, default=None
    )
    confirmation_email_2 = models.EmailField(
        max_length=44, null=True, blank=True, default=None
    )
    state = models.TextField(null=True, blank=True)
    zip = models.TextField(null=True, blank=True)
    report_code = models.TextField(null=True, blank=True)
    election_code = models.TextField(null=True, blank=True)
    date_of_election = models.DateField(null=True, blank=True)
    state_of_election = models.TextField(null=True, blank=True)
    coverage_from_date = models.DateField(null=True, blank=True)
    coverage_through_date = models.DateField(null=True, blank=True)
    qualified_committee = models.BooleanField(default=False, null=True, blank=True)
    treasurer_last_name = models.TextField(null=True, blank=True)
    treasurer_first_name = models.TextField(null=True, blank=True)
    treasurer_middle_name = models.TextField(null=True, blank=True)
    treasurer_prefix = models.TextField(null=True, blank=True)
    treasurer_suffix = models.TextField(null=True, blank=True)
    date_signed = models.DateField(null=True, blank=True)
    cash_on_hand_date = models.DateField(null=True, blank=True)
    L6b_cash_on_hand_beginning_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L6c_total_receipts_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L6d_subtotal_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L7_total_disbursements_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L8_cash_on_hand_at_close_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L9_debts_to_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L10_debts_by_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11ai_itemized_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11aii_unitemized_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11aiii_total_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11b_political_party_committees_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11c_other_political_committees_pacs_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11d_total_contributions_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L12_transfers_from_affiliated_other_party_cmtes_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L13_all_loans_received_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L14_loan_repayments_received_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L15_offsets_to_operating_expenditures_refunds_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L16_refunds_of_federal_contributions_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L17_other_federal_receipts_dividends_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L18a_transfers_from_nonfederal_account_h3_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L18b_transfers_from_nonfederal_levin_h5_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L18c_total_nonfederal_transfers_18a_18b_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L19_total_receipts_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L20_total_federal_receipts_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L21ai_federal_share_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L21aii_nonfederal_share_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L21b_other_federal_operating_expenditures_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L21c_total_operating_expenditures_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L22_transfers_to_affiliated_other_party_cmtes_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L23_contributions_to_federal_candidates_cmtes_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L24_independent_expenditures_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L25_coordinated_expend_made_by_party_cmtes_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L26_loan_repayments_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L27_loans_made_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L28a_individuals_persons_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L28b_political_party_committees_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L28c_other_political_committees_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L28d_total_contributions_refunds_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L29_other_disbursements_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L30ai_shared_federal_activity_h6_fed_share_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L30aii_shared_federal_activity_h6_nonfed_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L30b_nonallocable_fed_election_activity_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L30c_total_federal_election_activity_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L31_total_disbursements_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L32_total_federal_disbursements_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L33_total_contributions_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L34_total_contribution_refunds_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L35_net_contributions_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L36_total_federal_operating_expenditures_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L37_offsets_to_operating_expenditures_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L38_net_operating_expenditures_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L6a_cash_on_hand_jan_1_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L6a_year_for_above_ytd = models.TextField(null=True, blank=True)
    L6c_total_receipts_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L6d_subtotal_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L7_total_disbursements_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L8_cash_on_hand_close_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11ai_itemized_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11aii_unitemized_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11aiii_total_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11b_political_party_committees_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11c_other_political_committees_pacs_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11d_total_contributions_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L12_transfers_from_affiliated_other_party_cmtes_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L13_all_loans_received_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L14_loan_repayments_received_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L15_offsets_to_operating_expenditures_refunds_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L16_refunds_of_federal_contributions_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L17_other_federal_receipts_dividends_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L18a_transfers_from_nonfederal_account_h3_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L18b_transfers_from_nonfederal_levin_h5_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L18c_total_nonfederal_transfers_18a_18b_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L19_total_receipts_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L20_total_federal_receipts_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L21ai_federal_share_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L21aii_nonfederal_share_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L21b_other_federal_operating_expenditures_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L21c_total_operating_expenditures_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L22_transfers_to_affiliated_other_party_cmtes_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L23_contributions_to_federal_candidates_cmtes_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L24_independent_expenditures_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L25_coordinated_expend_made_by_party_cmtes_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L26_loan_repayments_made_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L27_loans_made_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L28a_individuals_persons_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L28b_political_party_committees_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L28c_other_political_committees_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L28d_total_contributions_refunds_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L29_other_disbursements_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L30ai_shared_federal_activity_h6_fed_share_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L30aii_shared_federal_activity_h6_nonfed_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L30b_nonallocable_fed_election_activity_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L30c_total_federal_election_activity_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L31_total_disbursements_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L32_total_federal_disbursements_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L33_total_contributions_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L34_total_contribution_refunds_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L35_net_contributions_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L36_total_federal_operating_expenditures_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L37_offsets_to_operating_expenditures_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L38_net_operating_expenditures_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )

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

    calculation_status = models.CharField(max_length=255, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Record if the is a create or update operation
        create_action = self.created is None

        with db_transaction.atomic():
            super(F3XSummary, self).save(*args, **kwargs)

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
            F3XSummary.objects.get_queryset()
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

    class Meta:
        db_table = "f3x_summaries"


class ReportMixin(models.Model):
    """Abstract model for tracking f3x reports

    Inherit this model to add an F3X Report foreign key, attributing
    a model instance to an F3X Report
    """

    report = models.ForeignKey(
        "f3x_summaries.F3XSummary", on_delete=models.CASCADE, null=True, blank=True
    )

    def save(self, *args, **kwargs):
        if self.report:
            committee = self.report.committee_account
            report_date = self.report.coverage_from_date
            if report_date is not None:
                report_year = report_date.year

                reports_to_flag_for_recalculation = F3XSummary.objects.filter(
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
                logger.info(f"F3X Summary: {report.id} marked for recalcuation")

        super(ReportMixin, self).save(*args, **kwargs)

    class Meta:
        abstract = True
