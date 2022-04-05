from django.db import models
from fecfiler.soft_delete.models import SoftDeleteModel


class F3XSummary(SoftDeleteModel):
    """Generated model from json schema"""

    form_type = models.TextField(null=True, blank=True)
    filer_committee_id_number = models.TextField(null=True, blank=True)
    committee_name = models.TextField(null=True, blank=True)
    change_of_address = models.BooleanField(default=False, null=True, blank=True)
    street_1 = models.TextField(null=True, blank=True)
    street_2 = models.TextField(null=True, blank=True)
    city = models.TextField(null=True, blank=True)

    state = models.TextField(null=True, blank=True)
    zip = models.TextField(null=True, blank=True)
    report_code = models.TextField(null=True, blank=True)
    election_code = models.TextField(null=True, blank=True)
    date_of_election = models.TextField(null=True, blank=True)
    state_of_election = models.TextField(null=True, blank=True)
    coverage_from_date = models.TextField(null=True, blank=True)
    coverage_through_date = models.TextField(null=True, blank=True)
    qualified_committee = models.BooleanField(default=False, null=True, blank=True)
    treasurer_last_name = models.TextField(null=True, blank=True)
    treasurer_first_name = models.TextField(null=True, blank=True)
    treasurer_middle_name = models.TextField(null=True, blank=True)
    treasurer_prefix = models.TextField(null=True, blank=True)
    treasurer_suffix = models.TextField(null=True, blank=True)
    date_signed = models.TextField(null=True, blank=True)
    L6b_cash_on_hand_beginning_period = models.IntegerField(null=True, blank=True)
    L6c_total_receipts_period = models.IntegerField(null=True, blank=True)
    L6d_subtotal_period = models.IntegerField(null=True, blank=True)
    L7_total_disbursements_period = models.IntegerField(null=True, blank=True)
    L8_cash_on_hand_at_close_period = models.IntegerField(null=True, blank=True)
    L9_debts_to_period = models.IntegerField(null=True, blank=True)
    L10_debts_by_period = models.IntegerField(null=True, blank=True)
    L11ai_itemized_period = models.IntegerField(null=True, blank=True)
    L11aii_unitemized_period = models.IntegerField(null=True, blank=True)
    L11aiii_total_period = models.IntegerField(null=True, blank=True)
    L11b_political_party_committees_period = models.IntegerField(null=True, blank=True)
    L11c_other_political_committees_pacs_period = models.IntegerField(
        null=True, blank=True
    )
    L11d_total_contributions_period = models.IntegerField(null=True, blank=True)
    L12_transfers_from_affiliated_other_party_cmtes_period = models.IntegerField(
        null=True, blank=True
    )
    L13_all_loans_received_period = models.IntegerField(null=True, blank=True)
    L14_loan_repayments_received_period = models.IntegerField(null=True, blank=True)
    L15_offsets_to_operating_expenditures_refunds_period = models.IntegerField(
        null=True, blank=True
    )
    L16_refunds_of_federal_contributions_period = models.IntegerField(
        null=True, blank=True
    )
    L17_other_federal_receipts_dividends_period = models.IntegerField(
        null=True, blank=True
    )
    L18a_transfers_from_nonfederal_account_h3_period = models.IntegerField(
        null=True, blank=True
    )
    L18b_transfers_from_nonfederal_levin_h5_period = models.IntegerField(
        null=True, blank=True
    )
    L18c_total_nonfederal_transfers_18a_18b_period = models.IntegerField(
        null=True, blank=True
    )
    L19_total_receipts_period = models.IntegerField(null=True, blank=True)
    L20_total_federal_receipts_period = models.IntegerField(null=True, blank=True)
    L21ai_federal_share_period = models.IntegerField(null=True, blank=True)
    L21aii_nonfederal_share_period = models.IntegerField(null=True, blank=True)
    L21b_other_federal_operating_expenditures_period = models.IntegerField(
        null=True, blank=True
    )
    L21c_total_operating_expenditures_period = models.IntegerField(
        null=True, blank=True
    )
    L22_transfers_to_affiliated_other_party_cmtes_period = models.IntegerField(
        null=True, blank=True
    )
    L23_contributions_to_federal_candidates_cmtes_period = models.IntegerField(
        null=True, blank=True
    )
    L24_independent_expenditures_period = models.IntegerField(null=True, blank=True)
    L25_coordinated_expend_made_by_party_cmtes_period = models.IntegerField(
        null=True, blank=True
    )
    L26_loan_repayments_period = models.IntegerField(null=True, blank=True)
    L27_loans_made_period = models.IntegerField(null=True, blank=True)
    L28a_individuals_persons_period = models.IntegerField(null=True, blank=True)
    L28b_political_party_committees_period = models.IntegerField(null=True, blank=True)
    L28c_other_political_committees_period = models.IntegerField(null=True, blank=True)
    L28d_total_contributions_refunds_period = models.IntegerField(null=True, blank=True)
    L29_other_disbursements_period = models.IntegerField(null=True, blank=True)
    L30ai_shared_federal_activity_h6_fed_share_period = models.IntegerField(
        null=True, blank=True
    )
    L30aii_shared_federal_activity_h6_nonfed_period = models.IntegerField(
        null=True, blank=True
    )
    L30b_nonallocable_fed_election_activity_period = models.IntegerField(
        null=True, blank=True
    )
    L30c_total_federal_election_activity_period = models.IntegerField(
        null=True, blank=True
    )
    L31_total_disbursements_period = models.IntegerField(null=True, blank=True)
    L32_total_federal_disbursements_period = models.IntegerField(null=True, blank=True)
    L33_total_contributions_period = models.IntegerField(null=True, blank=True)
    L34_total_contribution_refunds_period = models.IntegerField(null=True, blank=True)
    L35_net_contributions_period = models.IntegerField(null=True, blank=True)
    L36_total_federal_operating_expenditures_period = models.IntegerField(
        null=True, blank=True
    )
    L37_offsets_to_operating_expenditures_period = models.IntegerField(
        null=True, blank=True
    )
    L38_net_operating_expenditures_period = models.IntegerField(null=True, blank=True)
    L6a_cash_on_hand_jan_1_ytd = models.IntegerField(null=True, blank=True)
    L6a_year_for_above_ytd = models.TextField(null=True, blank=True)
    L6c_total_receipts_ytd = models.IntegerField(null=True, blank=True)
    L6d_subtotal_ytd = models.IntegerField(null=True, blank=True)
    L7_total_disbursements_ytd = models.IntegerField(null=True, blank=True)
    L8_cash_on_hand_close_ytd = models.IntegerField(null=True, blank=True)
    L11ai_itemized_ytd = models.IntegerField(null=True, blank=True)
    L11aii_unitemized_ytd = models.IntegerField(null=True, blank=True)
    L11aiii_total_ytd = models.IntegerField(null=True, blank=True)
    L11b_political_party_committees_ytd = models.IntegerField(null=True, blank=True)
    L11c_other_political_committees_pacs_ytd = models.IntegerField(
        null=True, blank=True
    )
    L11d_total_contributions_ytd = models.IntegerField(null=True, blank=True)
    L12_transfers_from_affiliated_other_party_cmtes_ytd = models.IntegerField(
        null=True, blank=True
    )
    L13_all_loans_received_ytd = models.IntegerField(null=True, blank=True)
    L14_loan_repayments_received_ytd = models.IntegerField(null=True, blank=True)
    L15_offsets_to_operating_expenditures_refunds_ytd = models.IntegerField(
        null=True, blank=True
    )
    L16_refunds_of_federal_contributions_ytd = models.IntegerField(
        null=True, blank=True
    )
    L17_other_federal_receipts_dividends_ytd = models.IntegerField(
        null=True, blank=True
    )
    L18a_transfers_from_nonfederal_account_h3_ytd = models.IntegerField(
        null=True, blank=True
    )
    L18b_transfers_from_nonfederal_levin_h5_ytd = models.IntegerField(
        null=True, blank=True
    )
    L18c_total_nonfederal_transfers_18a_18b_ytd = models.IntegerField(
        null=True, blank=True
    )
    L19_total_receipts_ytd = models.IntegerField(null=True, blank=True)
    L20_total_federal_receipts_ytd = models.IntegerField(null=True, blank=True)
    L21ai_federal_share_ytd = models.IntegerField(null=True, blank=True)
    L21aii_nonfederal_share_ytd = models.IntegerField(null=True, blank=True)
    L21b_other_federal_operating_expenditures_ytd = models.IntegerField(
        null=True, blank=True
    )
    L21c_total_operating_expenditures_ytd = models.IntegerField(null=True, blank=True)
    L22_transfers_to_affiliated_other_party_cmtes_ytd = models.IntegerField(
        null=True, blank=True
    )
    L23_contributions_to_federal_candidates_cmtes_ytd = models.IntegerField(
        null=True, blank=True
    )
    L24_independent_expenditures_ytd = models.IntegerField(null=True, blank=True)
    L25_coordinated_expend_made_by_party_cmtes_ytd = models.IntegerField(
        null=True, blank=True
    )
    L26_loan_repayments_made_ytd = models.IntegerField(null=True, blank=True)
    L27_loans_made_ytd = models.IntegerField(null=True, blank=True)
    L28a_individuals_persons_ytd = models.IntegerField(null=True, blank=True)
    L28b_political_party_committees_ytd = models.IntegerField(null=True, blank=True)
    L28c_other_political_committees_ytd = models.IntegerField(null=True, blank=True)
    L28d_total_contributions_refunds_ytd = models.IntegerField(null=True, blank=True)
    L29_other_disbursements_ytd = models.IntegerField(null=True, blank=True)
    L30ai_shared_federal_activity_h6_fed_share_ytd = models.IntegerField(
        null=True, blank=True
    )
    L30aii_shared_federal_activity_h6_nonfed_ytd = models.IntegerField(
        null=True, blank=True
    )
    L30b_nonallocable_fed_election_activity_ytd = models.IntegerField(
        null=True, blank=True
    )
    L30c_total_federal_election_activity_ytd = models.IntegerField(
        null=True, blank=True
    )
    L31_total_disbursements_ytd = models.IntegerField(null=True, blank=True)
    L32_total_federal_disbursements_ytd = models.IntegerField(null=True, blank=True)
    L33_total_contributions_ytd = models.IntegerField(null=True, blank=True)
    L34_total_contribution_refunds_ytd = models.IntegerField(null=True, blank=True)
    L35_net_contributions_ytd = models.IntegerField(null=True, blank=True)
    L36_total_federal_operating_expenditures_ytd = models.IntegerField(
        null=True, blank=True
    )
    L37_offsets_to_operating_expenditures_ytd = models.IntegerField(
        null=True, blank=True
    )
    L38_net_operating_expenditures_ytd = models.IntegerField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    committee_account_id = models.ForeignKey(
        'committee_accounts.CommitteeAccount', on_delete=models.CASCADE)

    class Meta:
        db_table = "f3x_summaries"
