from .models import F3XSummary
from rest_framework import serializers, exceptions
from fecfile_validate import validate
from functools import reduce
import logging

logger = logging.getLogger(__name__)


class F3XSummarySerializer(serializers.ModelSerializer):
    def validate(self, data):
        """Overrides Django Rest Framework's Serializer validate to validate with
        fecfile_validate rules.

        We need to translate the list of fecfile validation errors to a dictionary
            of ```path``` -> ```message``` to comply with DJR's validation error
            pattern
        """
        validation_result = validate.validate("F3X", data)
        if validation_result.errors:

            def collect_error(all_errors, error):
                all_errors[error.path] = error.message
                return all_errors

            translated_errors = reduce(collect_error, validation_result.errors, {})
            logger.warning(
                f"F3X Summary: Failed validation for {list(translated_errors)}"
            )
            raise exceptions.ValidationError(translated_errors)
        return data

    class Meta:
        model = F3XSummary
        fields = [
            "id",
            "form_type",
            "filer_committee_id_number",
            "committee_name",
            "change_of_address",
            "street_1",
            "street_2",
            "city",
            "state",
            "zip",
            "report_code",
            "election_code",
            "date_of_election",
            "state_of_election",
            "coverage_from_date",
            "coverage_through_date",
            "qualified_committee",
            "treasurer_last_name",
            "treasurer_first_name",
            "treasurer_middle_name",
            "treasurer_prefix",
            "treasurer_suffix",
            "date_signed",
            "L6b_cash_on_hand_beginning_period",
            "L6c_total_receipts_period",
            "L6d_subtotal_period",
            "L7_total_disbursements_period",
            "L8_cash_on_hand_at_close_period",
            "L9_debts_to_period",
            "L10_debts_by_period",
            "L11ai_itemized_period",
            "L11aii_unitemized_period",
            "L11aiii_total_period",
            "L11b_political_party_committees_period",
            "L11c_other_political_committees_pacs_period",
            "L11d_total_contributions_period",
            "L12_transfers_from_affiliated_other_party_cmtes_period",
            "L13_all_loans_received_period",
            "L14_loan_repayments_received_period",
            "L15_offsets_to_operating_expenditures_refunds_period",
            "L16_refunds_of_federal_contributions_period",
            "L17_other_federal_receipts_dividends_period",
            "L18a_transfers_from_nonfederal_account_h3_period",
            "L18b_transfers_from_nonfederal_levin_h5_period",
            "L18c_total_nonfederal_transfers_18a_18b_period",
            "L19_total_receipts_period",
            "L20_total_federal_receipts_period",
            "L21ai_federal_share_period",
            "L21aii_nonfederal_share_period",
            "L21b_other_federal_operating_expenditures_period",
            "L21c_total_operating_expenditures_period",
            "L22_transfers_to_affiliated_other_party_cmtes_period",
            "L23_contributions_to_federal_candidates_cmtes_period",
            "L24_independent_expenditures_period",
            "L25_coordinated_expend_made_by_party_cmtes_period",
            "L26_loan_repayments_period",
            "L27_loans_made_period",
            "L28a_individuals_persons_period",
            "L28b_political_party_committees_period",
            "L28c_other_political_committees_period",
            "L28d_total_contributions_refunds_period",
            "L29_other_disbursements_period",
            "L30ai_shared_federal_activity_h6_fed_share_period",
            "L30aii_shared_federal_activity_h6_nonfed_period",
            "L30b_nonallocable_fed_election_activity_period",
            "L30c_total_federal_election_activity_period",
            "L31_total_disbursements_period",
            "L32_total_federal_disbursements_period",
            "L33_total_contributions_period",
            "L34_total_contribution_refunds_period",
            "L35_net_contributions_period",
            "L36_total_federal_operating_expenditures_period",
            "L37_offsets_to_operating_expenditures_period",
            "L38_net_operating_expenditures_period",
            "L6a_cash_on_hand_jan_1_ytd",
            "L6a_year_for_above_ytd",
            "L6c_total_receipts_ytd",
            "L6d_subtotal_ytd",
            "L7_total_disbursements_ytd",
            "L8_cash_on_hand_close_ytd",
            "L11ai_itemized_ytd",
            "L11aii_unitemized_ytd",
            "L11aiii_total_ytd",
            "L11b_political_party_committees_ytd",
            "L11c_other_political_committees_pacs_ytd",
            "L11d_total_contributions_ytd",
            "L12_transfers_from_affiliated_other_party_cmtes_ytd",
            "L13_all_loans_received_ytd",
            "L14_loan_repayments_received_ytd",
            "L15_offsets_to_operating_expenditures_refunds_ytd",
            "L16_refunds_of_federal_contributions_ytd",
            "L17_other_federal_receipts_dividends_ytd",
            "L18a_transfers_from_nonfederal_account_h3_ytd",
            "L18b_transfers_from_nonfederal_levin_h5_ytd",
            "L18c_total_nonfederal_transfers_18a_18b_ytd",
            "L19_total_receipts_ytd",
            "L20_total_federal_receipts_ytd",
            "L21ai_federal_share_ytd",
            "L21aii_nonfederal_share_ytd",
            "L21b_other_federal_operating_expenditures_ytd",
            "L21c_total_operating_expenditures_ytd",
            "L22_transfers_to_affiliated_other_party_cmtes_ytd",
            "L23_contributions_to_federal_candidates_cmtes_ytd",
            "L24_independent_expenditures_ytd",
            "L25_coordinated_expend_made_by_party_cmtes_ytd",
            "L26_loan_repayments_made_ytd",
            "L27_loans_made_ytd",
            "L28a_individuals_persons_ytd",
            "L28b_political_party_committees_ytd",
            "L28c_other_political_committees_ytd",
            "L28d_total_contributions_refunds_ytd",
            "L29_other_disbursements_ytd",
            "L30ai_shared_federal_activity_h6_fed_share_ytd",
            "L30aii_shared_federal_activity_h6_nonfed_ytd",
            "L30b_nonallocable_fed_election_activity_ytd",
            "L30c_total_federal_election_activity_ytd",
            "L31_total_disbursements_ytd",
            "L32_total_federal_disbursements_ytd",
            "L33_total_contributions_ytd",
            "L34_total_contribution_refunds_ytd",
            "L35_net_contributions_ytd",
            "L36_total_federal_operating_expenditures_ytd",
            "L37_offsets_to_operating_expenditures_ytd",
            "L38_net_operating_expenditures_ytd",
            "created",
            "updated",
        ]
        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
