from django.db import transaction
from fecfiler.reports.models import Report
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.reports.serializers import (
    ReportSerializer,
)
from fecfiler.shared.utilities import get_model_data
from rest_framework.serializers import (
    CharField,
    DecimalField,
    BooleanField,
)
from fecfiler.reports.form_3.serializers import BaseForm3Serializer
import structlog

logger = structlog.get_logger(__name__)


class Form3XSerializer(BaseForm3Serializer):
    schema_name = "F3X"
    related_form_attr = "form_3x"

    filing_frequency = CharField(required=False, allow_null=True)

    qualified_committee = BooleanField(required=False, allow_null=True)
    L6b_cash_on_hand_beginning_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L6c_total_receipts_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L6d_subtotal_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L7_total_disbursements_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L8_cash_on_hand_at_close_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L9_debts_to_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L10_debts_by_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11ai_itemized_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11aii_unitemized_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11aiii_total_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11b_political_party_committees_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11c_other_political_committees_pacs_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11d_total_contributions_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L12_transfers_from_affiliated_other_party_cmtes_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L13_all_loans_received_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L14_loan_repayments_received_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L15_offsets_to_operating_expenditures_refunds_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L16_refunds_of_federal_contributions_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L17_other_federal_receipts_dividends_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L18a_transfers_from_nonfederal_account_h3_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L18b_transfers_from_nonfederal_levin_h5_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L18c_total_nonfederal_transfers_18a_18b_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L19_total_receipts_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L20_total_federal_receipts_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L21ai_federal_share_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L21aii_nonfederal_share_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L21b_other_federal_operating_expenditures_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L21c_total_operating_expenditures_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L22_transfers_to_affiliated_other_party_cmtes_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L23_contributions_to_federal_candidates_cmtes_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L24_independent_expenditures_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L25_coordinated_expend_made_by_party_cmtes_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L26_loan_repayments_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L27_loans_made_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L28a_individuals_persons_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L28b_political_party_committees_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L28c_other_political_committees_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L28d_total_contributions_refunds_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L29_other_disbursements_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L30ai_shared_federal_activity_h6_fed_share_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L30aii_shared_federal_activity_h6_nonfed_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L30b_nonallocable_fed_election_activity_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L30c_total_federal_election_activity_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L31_total_disbursements_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L32_total_federal_disbursements_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L33_total_contributions_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L34_total_contribution_refunds_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L35_net_contributions_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L36_total_federal_operating_expenditures_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L37_offsets_to_operating_expenditures_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L38_net_operating_expenditures_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L6a_cash_on_hand_jan_1_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L6a_year_for_above_ytd = CharField(required=False, allow_null=True)
    L6c_total_receipts_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L6d_subtotal_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L7_total_disbursements_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L8_cash_on_hand_close_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11ai_itemized_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11aii_unitemized_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11aiii_total_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11b_political_party_committees_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11c_other_political_committees_pacs_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11d_total_contributions_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L12_transfers_from_affiliated_other_party_cmtes_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L13_all_loans_received_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L14_loan_repayments_received_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L15_offsets_to_operating_expenditures_refunds_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L16_refunds_of_federal_contributions_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L17_other_federal_receipts_dividends_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L18a_transfers_from_nonfederal_account_h3_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L18b_transfers_from_nonfederal_levin_h5_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L18c_total_nonfederal_transfers_18a_18b_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L19_total_receipts_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L20_total_federal_receipts_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L21ai_federal_share_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L21aii_nonfederal_share_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L21b_other_federal_operating_expenditures_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L21c_total_operating_expenditures_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L22_transfers_to_affiliated_other_party_cmtes_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L23_contributions_to_federal_candidates_cmtes_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L24_independent_expenditures_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L25_coordinated_expend_made_by_party_cmtes_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L26_loan_repayments_made_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L27_loans_made_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L28a_individuals_persons_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L28b_political_party_committees_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L28c_other_political_committees_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L28d_total_contributions_refunds_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L29_other_disbursements_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L30ai_shared_federal_activity_h6_fed_share_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L30aii_shared_federal_activity_h6_nonfed_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L30b_nonallocable_fed_election_activity_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L30c_total_federal_election_activity_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L31_total_disbursements_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L32_total_federal_disbursements_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L33_total_contributions_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L34_total_contribution_refunds_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L35_net_contributions_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L36_total_federal_operating_expenditures_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L37_offsets_to_operating_expenditures_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L38_net_operating_expenditures_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )

    def create(self, validated_data: dict):
        with transaction.atomic():
            form_3x_data = get_model_data(validated_data, Form3X)
            report_data = get_model_data(validated_data, Report)
            form_3x = Form3X.objects.create(**form_3x_data)
            report_data["form_3x_id"] = form_3x.id
            report = super().create(report_data)
            return report

    class Meta(ReportSerializer.Meta):
        fields = (
            ReportSerializer.Meta.get_fields()
            + [f.name for f in Form3X._meta.get_fields() if f.name not in ["report"]]
            + ["fields_to_validate"]
        )

        read_only_fields = ["id", "created", "updated"]
