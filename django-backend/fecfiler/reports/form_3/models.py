import uuid
from django.db import models
import structlog

logger = structlog.get_logger(__name__)


class Form3(models.Model):

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    change_of_address = models.BooleanField(default=False, null=True, blank=True)

    """ not to be confused with state_of_election below...
    There are two distinct fields according to the FEC Spec"""
    election_state = models.TextField(null=True, blank=True)
    election_district = models.TextField(null=True, blank=True)

    election_code = models.TextField(null=True, blank=True)
    date_of_election = models.DateField(null=True, blank=True)
    state_of_election = models.TextField(null=True, blank=True)

    L6a_total_contributions_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L6b_total_contribution_refunds_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L6c_net_contributions_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L7a_total_operating_expenditures_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L7b_total_offsets_to_operating_expenditures_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L7c_net_operating_expenditures_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L8_cash_on_hand_at_close_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L9_debts_owed_to_committee_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L10_debts_owed_by_committee_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11ai_individuals_itemized_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11aii_individuals_unitemized_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11aiii_total_individual_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11b_political_party_committees_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11c_other_political_committees_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11d_the_candidate_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11e_total_contributions_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L12_transfers_from_other_authorized_committees_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L13a_loans_made_or_guaranteed_by_the_candidate_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L13b_all_other_loans_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L13c_total_loans_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L14_offsets_to_operating_expenditures_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L15_other_receipts_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L16_total_receipts_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L17_operating_expenditures_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L18_transfers_to_other_authorized_committees_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L19a_loan_repayments_of_loans_made_or_guaranteed_by_candidate_period = (
        models.DecimalField(
            null=True,
            blank=True,
            max_digits=11,
            decimal_places=2,
            db_column="l19a_period",
        )
    )
    L19b_loan_repayments_of_all_other_loans_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L19c_total_loan_repayments_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L20a_refunds_to_individuals_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L20b_refunds_to_political_party_committees_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L20c_refunds_to_other_political_committees_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L20d_total_contribution_refunds_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L21_other_disbursements_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L22_total_disbursements_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L23_cash_on_hand_beginning_reporting_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L24_total_receipts_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L25_subtotals_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L26_total_disbursements_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L27_cash_on_hand_at_close_period = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L6a_total_contributions_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L6b_total_contribution_refunds_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L6c_net_contributions_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L7a_total_operating_expenditures_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L7b_total_offsets_to_operating_expenditures_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L7c_net_operating_expenditures_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11ai_individuals_itemized_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11aii_individuals_unitemized_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11aiii_total_individual_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11b_political_party_committees_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11c_other_political_committees_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11d_the_candidate_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L11e_total_contributions_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L12_transfers_from_other_authorized_committees_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L13a_loans_made_or_guaranteed_by_the_candidate_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L13b_all_other_loans_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L13c_total_loans_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L14_offsets_to_operating_expenditures_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L15_other_receipts_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L16_total_receipts_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L17_operating_expenditures_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L18_transfers_to_other_authorized_committees_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L19a_loan_repayments_of_loans_made_or_guaranteed_by_candidate_ytd = (
        models.DecimalField(
            null=True, blank=True, max_digits=11, decimal_places=2, db_column="l19a_ytd"
        )
    )
    L19b_loan_repayments_of_all_other_loans_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L19c_total_loan_repayments_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L20a_refunds_to_individuals_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L20b_refunds_to_political_party_committees_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L20c_refunds_to_other_political_committees_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L20d_total_contribution_refunds_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L21_other_disbursements_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    L22_total_disbursements_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )

    class Meta:
        app_label = "reports"
