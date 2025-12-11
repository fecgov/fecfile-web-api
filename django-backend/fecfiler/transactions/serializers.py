from django.db.models import Sum
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.memo_text.serializers import LinkedMemoTextSerializerMixin
from fecfiler.validation.serializers import FecSchemaValidatorSerializerMixin
from fecfiler.reports.serializers import ReportSerializer
from fecfiler.contacts.serializers import ContactSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import empty, ModelSerializer
from collections import OrderedDict
from rest_framework.serializers import (
    BooleanField,
    UUIDField,
    CharField,
    DateField,
    DecimalField,
)
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.serializers import ScheduleASerializer
from fecfiler.transactions.schedule_b.serializers import ScheduleBSerializer
from fecfiler.transactions.schedule_c.serializers import ScheduleCSerializer
from fecfiler.transactions.schedule_c1.serializers import ScheduleC1Serializer
from fecfiler.transactions.schedule_c2.serializers import ScheduleC2Serializer
from fecfiler.transactions.schedule_d.serializers import ScheduleDSerializer
from fecfiler.transactions.schedule_e.serializers import ScheduleESerializer
from fecfiler.transactions.schedule_f.serializers import ScheduleFSerializer
from fecfiler.transactions.schedule_a.utils import add_schedule_a_contact_fields
from fecfiler.transactions.schedule_b.utils import add_schedule_b_contact_fields
from fecfiler.transactions.schedule_c.utils import add_schedule_c_contact_fields
from fecfiler.transactions.schedule_c1.utils import add_schedule_c1_contact_fields
from fecfiler.transactions.schedule_c2.utils import add_schedule_c2_contact_fields
from fecfiler.transactions.schedule_d.utils import add_schedule_d_contact_fields
from fecfiler.transactions.schedule_e.utils import add_schedule_e_contact_fields
from fecfiler.transactions.schedule_f.utils import add_schedule_f_contact_fields

from fecfiler.reports.report_code_label import get_report_code_label
import structlog

logger = structlog.get_logger(__name__)

MISSING_SCHEMA_NAME_ERROR = ValidationError({"schema_name": ["No schema_name provided"]})

SCHEDULE_SERIALIZERS = dict(
    A=ScheduleASerializer,
    B=ScheduleBSerializer,
    C=ScheduleCSerializer,
    C1=ScheduleC1Serializer,
    C2=ScheduleC2Serializer,
    D=ScheduleDSerializer,
    E=ScheduleESerializer,
    F=ScheduleFSerializer,
)

REATTRIBUTED = "REATTRIBUTED"
REDESIGNATED = "REDESIGNATED"
REATTRIBUTION_TO = "REATTRIBUTION_TO"
REDESIGNATION_TO = "REDESIGNATION_TO"


class TransactionSerializer(
    LinkedMemoTextSerializerMixin,
    FecSchemaValidatorSerializerMixin,
    CommitteeOwnedSerializer,
):
    """id must be explicitly configured in order to have it in validated_data
    https://github.com/encode/django-rest-framework/issues/2320#issuecomment-67502474"""

    id = UUIDField(required=False)

    schedule_a = ScheduleASerializer(read_only=True)
    schedule_b = ScheduleBSerializer(read_only=True)
    schedule_c = ScheduleCSerializer(read_only=True)
    schedule_c1 = ScheduleC1Serializer(read_only=True)
    schedule_c2 = ScheduleC2Serializer(read_only=True)
    schedule_d = ScheduleDSerializer(read_only=True)
    schedule_e = ScheduleESerializer(read_only=True)
    schedule_f = ScheduleFSerializer(read_only=True)

    contact_1_id = UUIDField(required=False, allow_null=True)
    contact_1 = ContactSerializer(read_only=True)
    contact_2_id = UUIDField(required=False, allow_null=True)
    contact_2 = ContactSerializer(read_only=True)
    contact_3_id = UUIDField(required=False, allow_null=True)
    contact_3 = ContactSerializer(read_only=True)
    contact_4_id = UUIDField(required=False, allow_null=True)
    contact_4 = ContactSerializer(read_only=True)
    contact_5_id = UUIDField(required=False, allow_null=True)
    contact_5 = ContactSerializer(read_only=True)

    back_reference_tran_id_number = CharField(
        required=False, allow_null=True, read_only=True
    )
    back_reference_sched_name = CharField(required=False, allow_null=True, read_only=True)
    form_type = CharField(required=False, allow_null=True)
    itemized = BooleanField(read_only=True)
    name = CharField(read_only=True)
    date = DateField(read_only=True)
    amount = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    debt_incurred_amount = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    aggregate = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    calendar_ytd_per_election_office = DecimalField(
        max_digits=11, decimal_places=2, read_only=True
    )
    aggregate_general_elec_expended = DecimalField(
        max_digits=11, decimal_places=2, read_only=True
    )
    balance = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    loan_payment_to_date = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    loan_balance = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    beginning_balance = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    payment_amount = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    balance_at_close = DecimalField(
        max_digits=11, decimal_places=2, read_only=True
    )  # debt payments
    line_label = CharField(read_only=True)
    report_code_label = CharField(read_only=True)

    class Meta:
        model = Transaction

        def get_fields():
            return [
                f.name
                for f in Transaction._meta.get_fields()
                if f.name
                not in [
                    "deleted",
                    "transaction",
                    "debt_associations",
                    "loan_associations",
                    "reatt_redes_associations",  # reattribution/redesignation
                    "reporttransaction",
                    "_form_type",
                    "blocking_reports",
                ]
            ] + [
                "parent_transaction_id",
                "debt_id",
                "loan_id",
                "reatt_redes_id",
                "contact_1_id",
                "contact_2_id",
                "contact_3_id",
                "contact_4_id",
                "contact_5_id",
                "memo_text_id",
                "back_reference_tran_id_number",
                "back_reference_sched_name",
                "form_type",
                "itemized",
                "fields_to_validate",
                "schema_name",
                "name",
                "date",
                "amount",
                "debt_incurred_amount",
                "aggregate",
                "calendar_ytd_per_election_office",
                "aggregate_general_elec_expended",
                "loan_payment_to_date",
                "balance",
                "loan_balance",
                "beginning_balance",
                "payment_amount",
                "balance_at_close",
                "line_label",
                "report_code_label",
            ]

        fields = get_fields()

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        self.handle_schedule_a(instance, representation)
        self.handle_schedule_b(instance, representation)
        self.handle_schedule_c(instance, representation)
        self.handle_schedule_f(instance, representation)
        self.handle_generic_schedule(
            instance, representation, "schedule_c1", add_schedule_c1_contact_fields
        )
        self.handle_generic_schedule(
            instance, representation, "schedule_c2", add_schedule_c2_contact_fields
        )
        self.handle_generic_schedule(
            instance, representation, "schedule_d", add_schedule_d_contact_fields
        )
        self.handle_generic_schedule(
            instance, representation, "schedule_e", add_schedule_e_contact_fields
        )

        # because form_type is a dynamic field
        representation["form_type"] = instance.form_type

        # represent parent
        if instance.parent_transaction:
            representation["parent_transaction"] = (
                TransactionSerializer().to_representation(instance.parent_transaction)
            )
        # represent loan
        if instance.loan:
            representation["loan"] = TransactionSerializer().to_representation(
                instance.loan
            )
        # represent debt
        if instance.debt:
            representation["debt"] = TransactionSerializer().to_representation(
                instance.debt
            )
        # represent original reattribution/redesignation transaction
        if instance.reatt_redes:
            representation["reatt_redes"] = TransactionSerializer().to_representation(
                instance.reatt_redes
            )

        representation["reports"] = []
        representation["report_ids"] = []
        for report in instance.reports.all():
            representation["report_ids"].append(report.id)
            representation["reports"].append(
                {
                    "id": report.id,
                    "coverage_from_date": report.coverage_from_date,
                    "coverage_through_date": report.coverage_through_date,
                    "report_code": report.report_code,
                    "report_type": report.report_type,
                    "report_code_label": get_report_code_label(report),
                }
            )

        representation["can_delete"] = instance.can_delete
        return representation

    def validate(self, data):
        initial_data = getattr(self, "initial_data")
        schedule_serializer = SCHEDULE_SERIALIZERS[initial_data.get("schedule_id")]
        data_to_validate = OrderedDict(
            [
                (field_name, (field.run_validation(field.get_value(initial_data))))
                for field_name, field in {
                    **self.fields,
                    **schedule_serializer(initial_data).fields,
                }.items()
                if (field.get_value(initial_data) is not empty and not field.read_only)
            ]
        )

        self._context["fields_to_ignore"] = self._context.get(
            "fields_to_ignore",
            [
                "filer_committee_id_number",
                "back_reference_tran_id_number",
                "contribution_aggregate",
                "aggregate_amount",
                "beginning_balance",
                "donor_candidate_fec_id",
                "beneficiary_candidate_fec_id",
                "beneficiary_candidate_last_name",
                "beneficiary_candidate_first_name",
                "beneficiary_candidate_office",
                "beneficiary_candidate_state",
            ],
        )
        super().validate(data_to_validate)
        return data

    def handle_schedule_a(self, instance, representation):
        schedule_a = representation.pop("schedule_a")
        if not schedule_a:
            return
        representation["contribution_aggregate"] = representation.get("aggregate")
        add_schedule_a_contact_fields(instance, representation)

        # For REATTRIBUTED transactions, calculate the amount that has
        # been reattributed for the transaction
        if instance.schedule_a.reattribution_redesignation_tag == REATTRIBUTED:
            total = (
                instance.reatt_redes_associations.filter(
                    schedule_a__reattribution_redesignation_tag=REATTRIBUTION_TO
                ).aggregate(Sum("schedule_a__contribution_amount"))[
                    "schedule_a__contribution_amount__sum"
                ]
                or 0.0
            )
            representation["reatt_redes_total"] = str(total)

        for property in schedule_a:
            if not representation.get(property):
                representation[property] = schedule_a[property]

    def handle_schedule_b(self, instance, representation):
        schedule_b = representation.pop("schedule_b")
        if not schedule_b:
            return
        representation["aggregate_amount"] = representation.get("aggregate")
        add_schedule_b_contact_fields(instance, representation)

        # For REDESIGNATED transactions, calculate the amount that has
        # been redesignated for the transaction
        if instance.schedule_b.reattribution_redesignation_tag == REDESIGNATED:
            total = (
                instance.reatt_redes_associations.filter(
                    schedule_b__reattribution_redesignation_tag=REDESIGNATION_TO
                ).aggregate(Sum("schedule_b__expenditure_amount"))[
                    "schedule_b__expenditure_amount__sum"
                ]
                or 0.0
            )
            representation["reatt_redes_total"] = str(total)

        for property in schedule_b:
            if not representation.get(property):
                representation[property] = schedule_b[property]

    def handle_schedule_c(self, instance, representation):
        schedule_c = representation.pop("schedule_c")
        if not schedule_c:
            return
        add_schedule_c_contact_fields(instance, representation)
        loan_agreement = instance.transaction_set.filter(
            transaction_type_identifier="C1_LOAN_AGREEMENT"
        ).first()
        representation["loan_agreement_id"] = (
            loan_agreement.id if loan_agreement else None
        )
        for property in schedule_c:
            if not representation.get(property):
                representation[property] = schedule_c[property]

    def handle_schedule_f(self, instance, representation):
        schedule_f = representation.pop("schedule_f")
        if not schedule_f:
            return

        add_schedule_f_contact_fields(instance, representation)

        for property in schedule_f:
            if not representation.get(property):
                representation[property] = schedule_f[property]

    def handle_generic_schedule(
        self, instance, representation, schedule_name, add_fields
    ):
        schedule = representation.pop(schedule_name)
        if not schedule:
            return
        add_fields(instance, representation)
        for property in schedule:
            if not representation.get(property):
                representation[property] = schedule[property]


class TransactionListSerializer(ModelSerializer):
    id = UUIDField()
    transaction_type_identifier = CharField(read_only=True)
    back_reference_tran_id_number = CharField(
        required=False, allow_null=True, read_only=True
    )
    form_type = CharField(required=False, allow_null=True)
    transaction_id = UUIDField(read_only=True)
    line_label = CharField(read_only=True)
    itemized = BooleanField(read_only=True)
    force_unaggregated = BooleanField(read_only=True)
    name = CharField(read_only=True)
    date = DateField(read_only=True)
    memo_code = BooleanField(read_only=True)
    amount = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    balance = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    aggregate = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    report_code_label = CharField(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            "id",
            "transaction_type_identifier",
            "back_reference_tran_id_number",
            "form_type",
            "transaction_id",
            "line_label",
            "itemized",
            "force_unaggregated",
            "name",
            "date",
            "memo_code",
            "amount",
            "balance",
            "aggregate",
            "report_code_label",
        ]


class TransactionReportSerializer(CommitteeOwnedSerializer):
    id = UUIDField(required=False)
    report = ReportSerializer(read_only=True)
    report_id = UUIDField(required=True, allow_null=False)
    transaction = TransactionSerializer(read_only=True)
    transaction_id = UUIDField(required=True, allow_null=False)
