import logging

from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.contacts.serializers import LinkedContactSerializerMixin
from fecfiler.memo_text.serializers import LinkedMemoTextSerializerMixin
from fecfiler.f3x_summaries.serializers import F3XSummarySerializer
from fecfiler.validation.serializers import FecSchemaValidatorSerializerMixin
from rest_framework.exceptions import ValidationError
from django.db.models import Q
from rest_framework.serializers import (
    BooleanField,
    UUIDField,
    CharField,
    DateField,
    ModelSerializer,
    DecimalField,
)
from fecfiler.contacts.models import Contact
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.transactions.schedule_b.models import ScheduleB
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.transactions.schedule_c2.models import ScheduleC2


logger = logging.getLogger(__name__)
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


class TransactionSerializerBase(
    LinkedContactSerializerMixin,
    LinkedMemoTextSerializerMixin,
    FecSchemaValidatorSerializerMixin,
    CommitteeOwnedSerializer,
):
    """id must be explicitly configured in order to have it in validated_data
    https://github.com/encode/django-rest-framework/issues/2320#issuecomment-67502474"""

    id = UUIDField(required=False)
    parent_transaction_id = UUIDField(required=False, allow_null=True)
    use_parent_contact = BooleanField(required=False, allow_null=True)
    transaction_id = CharField(required=False, allow_null=True)
    report_id = UUIDField(required=True, allow_null=False)
    report = F3XSummarySerializer(read_only=True)
    form_type = CharField(required=False, allow_null=True)
    itemized = BooleanField(read_only=True)
    date = DateField(read_only=True)
    amount = DecimalField(max_digits=11, decimal_places=2, read_only=True)
    aggregate = DecimalField(max_digits=11, decimal_places=2, read_only=True)

    schedule_a = ScheduleASerializer(required=False)
    schedule_b = ScheduleBSerializer(required=False)
    schedule_c = ScheduleCSerializer(required=False)
    schedule_c1 = ScheduleC1Serializer(required=False)
    schedule_c2 = ScheduleC2Serializer(required=False)

    def get_schema_name(self, data):
        schema_name = data.get("schema_name", None)
        if not schema_name:
            raise MISSING_SCHEMA_NAME_ERROR
        return schema_name

    def to_representation(self, instance, depth=0):
        representation = super().to_representation(instance)
        schedule_a = representation.pop("schedule_a") or []
        schedule_b = representation.pop("schedule_b") or []
        schedule_c = representation.pop("schedule_c") or []
        schedule_c1 = representation.pop("schedule_c1") or []
        schedule_c2 = representation.pop("schedule_c2") or []
        if (
            not hasattr(representation, "children")
            and depth < 2
            and instance.children.count() > 0
        ):
            representation["children"] = [
                self.to_representation(child, depth + 1) for child in instance.children
            ]

        if schedule_a:
            representation["contribution_aggregate"] = representation.get("aggregate")
            for property in schedule_a:
                if not representation.get(property):
                    representation[property] = schedule_a[property]
        if schedule_b:
            representation["aggregate_amount"] = representation.get("aggregate")
            for property in schedule_b:
                if not representation.get(property):
                    representation[property] = schedule_b[property]
        if schedule_c:
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

        representation["form_type"] = instance.form_type

        return representation

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        if internal_value.get("form_type"):
            internal_value["_form_type"] = internal_value["form_type"]
        return internal_value

    def propagate_contacts(self, transaction):
        contact_1 = Contact.objects.get(id=transaction.contact_1_id)
        self.propagate_contact(transaction, contact_1)
        contact_2 = Contact.objects.filter(id=transaction.contact_2_id).first()
        if contact_2:
            self.propagate_contact(transaction, contact_2)

    def propagate_contact(self, transaction, contact):
        subsequent_transactions = Transaction.objects.filter(
            ~Q(id=transaction.id),
            Q(Q(report__upload_submission__isnull=True)),
            Q(Q(contact_1=contact) | Q(contact_2=contact)),
            date__gte=transaction.get_date(),
        )
        for subsequent_transaction in subsequent_transactions:
            subsequent_transaction.get_schedule().update_with_contact(contact)
            subsequent_transaction.save()

    def validate(self, data):
        self.context["fields_to_ignore"] = self.context.get(
            "fields_to_ignore", ["filer_committee_id_number"]
        )
        return super().validate(data)

    class Meta:
        model = Transaction

        def get_fields():
            return [
                f.name
                for f in Transaction._meta.get_fields()
                if f.name not in ["deleted", "transaction", "parent_transaction"]
            ] + [
                "parent_transaction_id",
                "use_parent_contact",
                "report_id",
                "contact_1_id",
                "contact_2_id",
                "memo_text_id",
                "form_type",
                "itemized",
                "fields_to_validate",
                "schema_name",
                "date",
                "amount",
                "aggregate",
                "schedule_a",
                "schedule_b",
                "schedule_c",
                "schedule_c1",
                "schedule_c2",
            ]

        fields = get_fields()
        read_only_fields = ["parent_transaction"]
