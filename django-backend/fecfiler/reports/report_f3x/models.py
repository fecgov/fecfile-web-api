import uuid
from django.db import models
import logging


logger = logging.getLogger(__name__)


class ReportF3X(models.Model):
    """Generated model from json schema"""

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    change_of_address = models.BooleanField(default=False, null=True, blank=True)
    street_1 = models.TextField(null=True, blank=True)
    street_2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)
    state = models.TextField(null=True, blank=True)
    zip = models.TextField(null=True, blank=True)
    election_code = models.TextField(null=True, blank=True)
    date_of_election = models.DateField(null=True, blank=True)
    state_of_election = models.TextField(null=True, blank=True)
    qualified_committee = models.BooleanField(default=False, null=True, blank=True)
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

    class Meta:
        app_label = "reports"
