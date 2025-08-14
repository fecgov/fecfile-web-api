from django.db import transaction
from fecfiler.reports.models import Report, ReportTransaction
from fecfiler.reports.form_3x.models import Form3X
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
from rest_framework.serializers import ValidationError
import structlog

logger = structlog.get_logger(__name__)

COVERAGE_DATES_EXCLUDE_EXISTING_TRANSACTIONS = ValidationError(
    {
        "coverage_from_date_and_coverage_to_date": [
            "Coverage date(s) exclude existing transaction(s) for report"
        ]
    }
)


class Form3XSerializer(ReportSerializer):
    schema_name = "F3X"

    filing_frequency = CharField(required=False, allow_null=True)
    report_type_category = CharField(required=False, allow_null=True)
    change_of_address = BooleanField(required=False, allow_null=True)
    election_code = CharField(required=False, allow_null=True)
    date_of_election = DateField(required=False, allow_null=True)
    state_of_election = CharField(required=False, allow_null=True)
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

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        report = ReportSerializer(context=self.context).to_internal_value(data)
        internal.update(report)
        return internal

    def create(self, validated_data: dict):
        with transaction.atomic():
            form_3x_data = get_model_data(validated_data, Form3X)
            report_data = get_model_data(validated_data, Report)
            form_3x_data["L6a_year_for_above_ytd"] = report_data[
                "coverage_from_date"
            ].year  # noqa: E501
            form_3x = Form3X.objects.create(**form_3x_data)
            report_data["form_3x_id"] = form_3x.id
            report = super().create(report_data)
            return report

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            # Check if there are any transactions that fall outside the coverage dates
            transactions_outside_coverage_dates = ReportTransaction.objects.filter(
                ~Q(transaction__memo_code=True),
                self.get_transaction_date_outside_coverage_dates_clause(),
                transaction__deleted=None,
                report_id=instance.id,
            ).count()
            if transactions_outside_coverage_dates > 0:
                raise COVERAGE_DATES_EXCLUDE_EXISTING_TRANSACTIONS

            # Check if there is any overlap in dates with other reports
            number_of_overlapping_reports = Report.objects.filter(
                ~Q(id=instance.id),
                Q(
                    coverage_from_date__gte=validated_data["coverage_from_date"],
                    coverage_from_date__lte=validated_data["coverage_through_date"]
                ) | Q(
                    coverage_through_date__gte=validated_data["coverage_from_date"],
                    coverage_through_date__lte=validated_data["coverage_through_date"]
                )
            ).count()
            if number_of_overlapping_reports > 0:
                raise COVERAGE_DATE_REPORT_CODE_COLLISION

            # Apply changes to the form_3x instance
            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.form_3x, attr, value)

            instance.form_3x.save()
            updated = super().update(instance, validated_data)
            return updated

    def save(self, **kwargs):
        """Raise a ValidationError if an F3X with the same report code
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
            return super(Form3XSerializer, self).save(**kwargs)
        else:
            raise COVERAGE_DATE_REPORT_CODE_COLLISION

    def validate(self, data):
        self._context = self.context.copy()
        self._context["fields_to_ignore"] = self._context.get(
            "fields_to_ignore", ["filer_committee_id_number"]
        )
        return super().validate(data)

    def get_transaction_date_outside_coverage_dates_clause(self):
        """Returns a clause that checks if the transaction date is outside
        the coverage dates for the report.
        """
        from_date = self.validated_data["coverage_from_date"]
        through_date = self.validated_data["coverage_through_date"]
        return Q(
            Q(
                Q(transaction__schedule_a__isnull=False),
                Q(
                    Q(transaction__schedule_a__contribution_date__lt=from_date)
                    | Q(transaction__schedule_a__contribution_date__gt=through_date)
                ),
            )
            | Q(
                Q(transaction__schedule_b__isnull=False),
                Q(
                    Q(transaction__schedule_b__expenditure_date__lt=from_date)
                    | Q(transaction__schedule_b__expenditure_date__gt=through_date)
                ),
            )
            | Q(
                Q(
                    transaction__schedule_c__isnull=False,
                    transaction__loan_id__isnull=True,
                ),
                Q(
                    Q(transaction__schedule_c__loan_incurred_date__lt=from_date)
                    | Q(transaction__schedule_c__loan_incurred_date__gt=through_date)
                ),
            )
            | Q(
                Q(transaction__schedule_e__isnull=False),
                Q(
                    Q(transaction__schedule_e__disbursement_date__lt=from_date)
                    | Q(transaction__schedule_e__disbursement_date__gt=through_date)
                ),
            )
            | Q(
                Q(transaction__schedule_e__isnull=False),
                Q(
                    Q(transaction__schedule_e__dissemination_date__lt=from_date)
                    | Q(transaction__schedule_e__dissemination_date__gt=through_date)
                ),
            )
            | Q(
                Q(transaction__schedule_f__isnull=False),
                Q(
                    Q(transaction__schedule_f__expenditure_date__lt=from_date)
                    | Q(transaction__schedule_f__expenditure_date__gt=through_date)
                ),
            )
        )

    class Meta(ReportSerializer.Meta):
        fields = (
            ReportSerializer.Meta.get_fields()
            + [f.name for f in Form3X._meta.get_fields() if f.name not in ["report"]]
            + ["fields_to_validate"]
        )

        read_only_fields = ["id", "created", "updated"]
