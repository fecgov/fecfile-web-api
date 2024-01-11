from django.db.models import Sum
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.contacts.serializers import LinkedContactSerializerMixin
from fecfiler.memo_text.serializers import LinkedMemoTextSerializerMixin
from fecfiler.validation.serializers import FecSchemaValidatorSerializerMixin
from fecfiler.reports.serializers import ReportSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import empty
from collections import OrderedDict
from rest_framework.serializers import (
    BooleanField,
    UUIDField,
    CharField,
    DateField,
    ModelSerializer,
    DecimalField,
)
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.transactions.schedule_e.models import ScheduleE
import structlog

logger = structlog.get_logger(__name__)

MISSING_SCHEMA_NAME_ERROR = ValidationError(
    {"schema_name": ["No schema_name provided"]}
)


class ScheduleASerializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in ScheduleA._meta.get_fields()
            if f.name not in ["deleted", "transaction"]
        ]
        model = ScheduleA


class ScheduleBSerializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in ScheduleB._meta.get_fields()
            if f.name not in ["deleted", "transaction"]
        ]
        model = ScheduleB


class ScheduleCSerializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in ScheduleC._meta.get_fields()
            if f.name not in ["deleted", "transaction"]
        ]
        model = ScheduleC


class ScheduleC1Serializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in ScheduleC1._meta.get_fields()
            if f.name not in ["deleted", "transaction"]
        ]
        model = ScheduleC1


class ScheduleC2Serializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in ScheduleC2._meta.get_fields()
            if f.name not in ["deleted", "transaction"]
        ]
        model = ScheduleC2


class ScheduleDSerializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in ScheduleD._meta.get_fields()
            if f.name not in ["deleted", "transaction"]
        ]
        model = ScheduleD


class ScheduleESerializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in ScheduleE._meta.get_fields()
            if f.name not in ["deleted", "transaction"]
        ]
        model = ScheduleE


SCHEDULE_SERIALIZERS = dict(
    A=ScheduleASerializer,
    B=ScheduleBSerializer,
    C=ScheduleCSerializer,
    C1=ScheduleC1Serializer,
    C2=ScheduleC2Serializer,
    D=ScheduleDSerializer,
    E=ScheduleESerializer,
)


class TransactionSerializer(
    LinkedContactSerializerMixin,
    LinkedMemoTextSerializerMixin,
    FecSchemaValidatorSerializerMixin,
    CommitteeOwnedSerializer,
):
    """id must be explicitly configured in order to have it in validated_data
    https://github.com/encode/django-rest-framework/issues/2320#issuecomment-67502474"""

    id = UUIDField(required=False)
    report_id = UUIDField(required=True, allow_null=False)
    schedule_a = ScheduleASerializer(required=False)
    schedule_b = ScheduleBSerializer(required=False)
    schedule_c = ScheduleCSerializer(required=False)
    schedule_c1 = ScheduleC1Serializer(required=False)
    schedule_c2 = ScheduleC2Serializer(required=False)
    schedule_d = ScheduleDSerializer(required=False)
    schedule_e = ScheduleESerializer(required=False)

    report = ReportSerializer(read_only=True)

    back_reference_tran_id_number = CharField(
        required=False, allow_null=True, read_only=True
    )
    back_reference_sched_name = CharField(
        required=False, allow_null=True, read_only=True
    )
    form_type = CharField(required=False, allow_null=True)
    itemized = BooleanField(read_only=True)
    name = CharField(read_only=True)
    date = DateField(read_only=True)
    amount = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    aggregate = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    calendar_ytd_per_election_office = DecimalField(
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
                    "_form_type",
                ]
            ] + [
                "parent_transaction_id",
                "debt_id",
                "loan_id",
                "reatt_redes_id",
                "report_id",
                "contact_1_id",
                "contact_2_id",
                "contact_3_id",
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
                "aggregate",
                "calendar_ytd_per_election_office",
                "loan_payment_to_date",
                "balance",
                "loan_balance",
                "beginning_balance",
                "payment_amount",
                "balance_at_close",
                "line_label",
            ]

        fields = get_fields()
        read_only_fields = ["children"]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        schedule_a = representation.pop("schedule_a")
        schedule_b = representation.pop("schedule_b")
        schedule_c = representation.pop("schedule_c")
        schedule_c1 = representation.pop("schedule_c1")
        schedule_c2 = representation.pop("schedule_c2")
        schedule_d = representation.pop("schedule_d")
        schedule_e = representation.pop("schedule_e")
        if instance.children.count() > 0:
            representation["children"] = [child.id for child in instance.children]

        if schedule_a:
            representation["contribution_aggregate"] = representation.get("aggregate")

            # For REATTRIBUTED transactions, calculate the amount that has
            # been reattributed for the transaction
            total = instance.reatt_redes_associations.filter(
                schedule_a__reattribution_redesignation_tag="REATTRIBUTION_TO"
            ).aggregate(Sum("amount"))['amount__sum'] or 0.0
            representation["reatt_redes_total"] = str(total)

            for property in schedule_a:
                if not representation.get(property):
                    representation[property] = schedule_a[property]
        if schedule_b:
            representation["aggregate_amount"] = representation.get("aggregate")

            # For REDESIGNATED transactions, calculate the amount that has
            # been redesignated for the transaction
            total = instance.reatt_redes_associations.filter(
                schedule_b__reattribution_redesignation_tag="REDESIGNATION_TO"
            ).aggregate(Sum("amount"))['amount__sum'] or 0.0
            representation["reatt_redes_total"] = str(total)

            for property in schedule_b:
                if not representation.get(property):
                    representation[property] = schedule_b[property]
        if schedule_c:
            loan_agreement = instance.children.filter(
                transaction_type_identifier="C1_LOAN_AGREEMENT"
            ).first()
            representation["loan_agreement_id"] = (
                loan_agreement.id if loan_agreement else None
            )
            for property in schedule_c:
                if not representation.get(property):
                    representation[property] = schedule_c[property]
        if schedule_c1:
            for property in schedule_c1:
                if not representation.get(property):
                    representation[property] = schedule_c1[property]
        if schedule_c2:
            for property in schedule_c2:
                if not representation.get(property):
                    representation[property] = schedule_c2[property]
        if schedule_d:
            for property in schedule_d:
                if not representation.get(property):
                    representation[property] = schedule_d[property]
        if schedule_e:
            for property in schedule_e:
                if not representation.get(property):
                    representation[property] = schedule_e[property]

        # because form_type is a dynamic field
        representation["form_type"] = instance.form_type

        # Assign the itemization value of the highest level parent for all transactions.
        # The itemization value of the parent (or any ancestor) is not yet calcuated
        # when retrieving this instance from the db.
        if instance.parent_transaction:
            if instance.parent_transaction.parent_transaction:
                itemized = Transaction.objects.get(
                    id=instance.parent_transaction.parent_transaction.id
                ).itemized
            else:
                parent = Transaction.objects.get(id=instance.parent_transaction.id)
                # Assign child IE's thier parent's calendar ytd per election
                if instance.schedule_e:
                    representation[
                        "calendar_ytd_per_election_office"
                    ] = parent.calendar_ytd_per_election_office
                itemized = parent.itemized
            representation["itemized"] = itemized

        # represent parent
        if instance.parent_transaction:
            representation[
                "parent_transaction"
            ] = TransactionSerializer().to_representation(instance.parent_transaction)
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
            ],
        )
        super().validate(data_to_validate)
        return data
