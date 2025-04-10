from django.db import transaction
from fecfiler.reports.models import Report
from fecfiler.reports.form_3.models import Form3
from fecfiler.reports.serializers import (
    ReportSerializer,
    COVERAGE_DATE_REPORT_CODE_COLLISION,
)
from fecfiler.shared.utilities import get_model_data
from django.db.models import Q
from rest_framework.serializers import (
    CharField,
    DecimalField,
    DateField,
    BooleanField,
)
import structlog

logger = structlog.get_logger(__name__)


class Form3Serializer(ReportSerializer):
    schema_name = "F3"

    change_of_address = BooleanField(required=False, allow_null=True)
    election_state = CharField(required=False, allow_null=True)
    election_district = CharField(required=False, allow_null=True)

    election_code = CharField(required=False, allow_null=True)
    date_of_election = DateField(required=False, allow_null=True)
    state_of_election = CharField(required=False, allow_null=True)

    L6a_total_contributions_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L6b_total_contribution_refunds_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L6c_net_contributions_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L7a_total_operating_expenditures_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L7b_total_offsets_to_operating_expenditures_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L7c_net_operating_expenditures_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L8_cash_on_hand_at_close_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L9_debts_owed_to_committee_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L10_debts_owed_by_committee_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11ai_individuals_itemized_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11aii_individuals_unitemized_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11aiii_total_individual_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11b_political_party_committees_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11c_other_political_committees_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11d_the_candidate_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11e_total_contributions_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L12_transfers_from_other_authorized_committees_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L13a_loans_made_or_guaranteed_by_the_candidate_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L13b_all_other_loans_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L13c_total_loans_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L14_offsets_to_operating_expenditures_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L15_other_receipts_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L16_total_receipts_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L17_operating_expenditures_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L18_transfers_to_other_authorized_committees_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L19a_loan_repayments_of_loans_made_or_guaranteed_by_candidate_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L19b_loan_repayments_of_all_other_loans_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L19c_total_loan_repayments_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L20a_refunds_to_individuals_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L20b_refunds_to_political_party_committees_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L20c_refunds_to_other_political_committees_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L20d_total_contribution_refunds_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L21_other_disbursements_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L22_total_disbursements_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L23_cash_on_hand_beginning_reporting_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L24_total_receipts_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L25_subtotals_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L26_total_disbursements_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L27_cash_on_hand_at_close_period = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L6a_total_contributions_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L6b_total_contribution_refunds_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L6c_net_contributions_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L7a_total_operating_expenditures_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L7b_total_offsets_to_operating_expenditures_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L7c_net_operating_expenditures_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11ai_individuals_itemized_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11aii_individuals_unitemized_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11aiii_total_individual_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11b_political_party_committees_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11c_other_political_committees_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11d_the_candidate_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L11e_total_contributions_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L12_transfers_from_other_authorized_committees_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L13a_loans_made_or_guaranteed_by_the_candidate_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L13b_all_other_loans_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L13c_total_loans_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L14_offsets_to_operating_expenditures_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L15_other_receipts_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L16_total_receipts_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L17_operating_expenditures_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L18_transfers_to_other_authorized_committees_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L19a_loan_repayments_of_loans_made_or_guaranteed_by_candidate_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L19b_loan_repayments_of_all_other_loans_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L19c_total_loan_repayments_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L20a_refunds_to_individuals_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L20b_refunds_to_political_party_committees_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L20c_refunds_to_other_political_committees_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L20d_total_contribution_refunds_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L21_other_disbursements_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )
    L22_total_disbursements_ytd = DecimalField(
        required=False, allow_null=True, max_digits=11, decimal_places=2
    )

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        report = ReportSerializer(context=self.context).to_internal_value(data)
        internal.update(report)
        return internal

    def create(self, validated_data: dict):
        with transaction.atomic():
            form_3_data = get_model_data(validated_data, Form3)
            report_data = get_model_data(validated_data, Report)
            form_3 = Form3.objects.create(**form_3_data)
            report_data["form_3_id"] = form_3.id
            report = super().create(report_data)
            return report

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.form_3, attr, value)
            instance.form_3.save()
            updated = super().update(instance, validated_data)
            return updated

    def save(self, **kwargs):
        """Raise a ValidationError if an F3 with the same report code
        exists for the same year
        """
        committee_uuid = self.get_committee_uuid()
        number_of_collisions = Report.objects.filter(
            ~Q(id=(self.instance or Report()).id),
            committee_account=committee_uuid,
            coverage_from_date__year=self.validated_data["coverage_from_date"].year,
            report_code=self.validated_data["report_code"],
        ).count()
        if number_of_collisions == 0:
            return super(Form3Serializer, self).save(**kwargs)
        else:
            raise COVERAGE_DATE_REPORT_CODE_COLLISION

    def validate(self, data):
        self._context = self.context.copy()
        self._context["fields_to_ignore"] = self._context.get(
            "fields_to_ignore", ["filer_committee_id_number"]
        )
        return super().validate(data)

    class Meta(ReportSerializer.Meta):
        fields = (
            ReportSerializer.Meta.get_fields()
            + [f.name for f in Form3._meta.get_fields() if f.name not in ["report"]]
            + ["fields_to_validate"]
        )

        read_only_fields = ["id", "created", "updated"]
