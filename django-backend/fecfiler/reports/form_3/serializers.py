from django.db import transaction
from fecfiler.reports.models import Report, ReportTransaction
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
from rest_framework.serializers import ValidationError
from datetime import date
import structlog

logger = structlog.get_logger(__name__)

COVERAGE_DATES_EXCLUDE_EXISTING_TRANSACTIONS = ValidationError(
    {
        "coverage_from_date_and_coverage_to_date": [
            "Coverage date(s) exclude existing transaction(s) for report"
        ]
    }
)


class BaseForm3Serializer(ReportSerializer):
    report_type_category = CharField(required=False, allow_null=True)
    change_of_address = BooleanField(required=False, allow_null=True)
    election_code = CharField(required=False, allow_null=True)
    date_of_election = DateField(required=False, allow_null=True)
    state_of_election = CharField(required=False, allow_null=True)

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        report = ReportSerializer(context=self.context).to_internal_value(data)
        internal.update(report)
        return internal

    def validate(self, data):
        self._context = self.context.copy()
        self._context["fields_to_ignore"] = self._context.get(
            "fields_to_ignore", ["filer_committee_id_number"]
        )
        return super().validate(data)

    def save(self, **kwargs):
        committee_uuid = self.get_committee_uuid()
        instance_id = self.instance.id if self.instance else None

        if self.overlaps_other_f3_report(
            instance_id,
            committee_uuid,
            self.validated_data,
        ):
            raise COVERAGE_DATE_REPORT_CODE_COLLISION

        return super().save(**kwargs)

    def update(self, instance, validated_data):
        prior_coverage_through_date = instance.coverage_through_date
        prior_coverage_from_date = instance.coverage_from_date

        transactions_outside_coverage_dates = ReportTransaction.objects.filter(
            ~Q(transaction__memo_code=True),
            self.get_transaction_date_outside_coverage_dates_clause(),
            transaction__deleted=None,
            report_id=instance.id,
        ).count()

        if transactions_outside_coverage_dates > 0:
            raise COVERAGE_DATES_EXCLUDE_EXISTING_TRANSACTIONS

        if self.overlaps_other_f3_report(
            instance.id,
            instance.committee_account.id,
            validated_data,
        ):
            raise COVERAGE_DATE_REPORT_CODE_COLLISION

        form = getattr(instance, self.related_form_attr)

        for attr, value in validated_data.items():
            if attr != "id":
                setattr(form, attr, value)

        form.save()

        updated = super().update(instance, validated_data)

        coverage_from_changed = prior_coverage_from_date != updated.coverage_from_date
        coverage_through_changed = (
            prior_coverage_through_date != updated.coverage_through_date
        )

        if coverage_from_changed or coverage_through_changed:
            Report.mark_calculations_dirty(Report.objects.filter(id=updated.id))

        return updated

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

    def overlaps_other_f3_report(self, instance_id, committee_uuid, validated_data):
        coverage_from_date = validated_data.get("coverage_from_date")
        coverage_year = None
        match (type(coverage_from_date)):
            case date.__class__:
                coverage_year = coverage_from_date.year
            case str.__class__:
                coverage_year = coverage_from_date[:4]

        return (
            Report.objects.filter(
                ~Q(id=instance_id),
                Q(committee_account__id=committee_uuid),
                Q(
                    coverage_from_date__gte=validated_data.get("coverage_from_date"),
                    coverage_from_date__lte=validated_data.get("coverage_through_date"),
                )
                | Q(
                    coverage_through_date__gte=validated_data.get("coverage_from_date"),
                    coverage_through_date__lte=validated_data.get(
                        "coverage_through_date"
                    ),
                )
                | Q(
                    coverage_from_date__year=coverage_year,
                    report_code=validated_data.get("report_code"),
                ),
            ).count()
            > 0
        )


class Form3Serializer(BaseForm3Serializer):
    schema_name = "F3"
    related_form_attr = "form_3"

    election_state = CharField(required=False, allow_null=True)
    election_district = CharField(required=False, allow_null=True)

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

    def create(self, validated_data: dict):
        with transaction.atomic():
            form_3_data = get_model_data(validated_data, Form3)
            report_data = get_model_data(validated_data, Report)
            form_3 = Form3.objects.create(**form_3_data)
            report_data["form_3_id"] = form_3.id
            report = super().create(report_data)
            return report

    class Meta(ReportSerializer.Meta):
        fields = (
            ReportSerializer.Meta.get_fields()
            + [f.name for f in Form3._meta.get_fields() if f.name not in ["report"]]
            + ["fields_to_validate"]
        )

        read_only_fields = ["id", "created", "updated"]
