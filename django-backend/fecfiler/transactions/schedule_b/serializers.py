import logging

from django.db import transaction
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.contacts.models import Contact
from fecfiler.memo_text.models import MemoText
from fecfiler.contacts.serializers import ContactSerializer
from fecfiler.memo_text.serializers import MemoTextSerializer
from fecfiler.transactions.serializers import TransactionSerializerBase
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import (
    BooleanField,
    DecimalField,
    ListSerializer,
    UUIDField,
    CharField,
)


from fecfiler.transactions.schedule_b.models import ScheduleBTransaction

logger = logging.getLogger(__name__)


class ScheduleBTransactionSerializerBase(TransactionSerializerBase):

    """These fields are generated in the query"""

    expenditure_aggregate = DecimalField(
        max_digits=11, decimal_places=2, read_only=True
    )

    def validate(self, attrs):
        """Adds stub contribution_aggregate to pass validation"""
        attrs["expenditure_aggregate"] = 0
        data = super().validate(attrs)
        del data["expenditure_aggregate"]
        return data

    class Meta:
        model = ScheduleBTransaction
        fields = [
            f.name
            for f in ScheduleBTransaction._meta.get_fields()
            if f.name not in ["deleted", "schedulebtransaction"]
        ] + [
            "report_id",
            "contact_id",
            "memo_text_id",
            "expenditure_aggregate",
            "itemized",
            "fields_to_validate",
        ]


class ScheduleBTransactionSerializer(ScheduleBTransactionSerializerBase):
    children = ListSerializer(
        child=ScheduleBTransactionSerializerBase(),
        allow_null=True,
        allow_empty=True,
        required=False,
    )

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        # Add child transactions to transaction.children field in JSON output
        existing_children = ScheduleBTransaction.objects.filter(
            parent_transaction_object_id=instance.id
        ).all()
        ret["children"] = map(self.to_representation, existing_children)
        return ret

    def to_internal_value(self, data):
        # We are not saving report or parent_transaction objects so
        # we need to ensure their object properties are UUIDs and not objects
        def insert_foreign_keys(transaction):
            transaction["report"] = transaction["report_id"]
            if "parent_transaction_object_id" in transaction:
                transaction["parent_transaction"] = transaction[
                    "parent_transaction_object_id"
                ]
            return transaction

        if "children" in data:
            data["children"] = list(map(insert_foreign_keys, data["children"]))
        return super().to_internal_value(data)

    def create(self, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_contact(validated_data)
            self.create_or_update_memo_text(validated_data)
            children = validated_data.pop("children", [])
            parent = super().create(validated_data)
            for child in children:
                child["parent_transaction_object_id"] = parent.id
                self.create(child)
            return parent

    def update(self, instance: ScheduleBTransaction, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_contact(validated_data)
            self.create_or_update_memo_text(validated_data)
            children = validated_data.pop("children", [])

            existing_children = ScheduleBTransaction.objects.filter(
                parent_transaction_object_id=instance.id
            ).all()
            for child in children:
                try:
                    """this will not make multiple db calls because
                    the existing_children queryset is cached
                    """
                    existing_child = existing_children.get(id=child.get("id", None))
                    self.update(existing_child, child)
                except ScheduleBTransaction.DoesNotExist:
                    self.create(child)
            return super().update(instance, validated_data)

    def create_or_update_contact(self, validated_data: dict):
        contact_data = validated_data.pop("contact", None)
        tran_contact_id = validated_data.get("contact_id", None)
        if not tran_contact_id:
            if not contact_data:
                raise ValidationError(
                    {"contact_id": ["No transaction contact or contact id provided"]}
                )
            contact: Contact = Contact.objects.create(**contact_data)
            validated_data["contact_id"] = contact.id
        else:
            Contact.objects.filter(id=tran_contact_id).update(**contact_data)

    def create_or_update_memo_text(self, validated_data: dict):
        memo_data = validated_data.pop("memo_text", None)
        tran_memo_text_id = validated_data.get("memo_text_id", None)
        if memo_data:
            memo_text, _ = MemoText.objects.update_or_create(
                id=tran_memo_text_id,
                defaults={
                    "is_report_level_memo": False,
                    "report_id": validated_data.get("report_id", None),
                    **memo_data,
                },
            )
            validated_data["memo_text_id"] = memo_text.id
        elif tran_memo_text_id:
            memo_object = MemoText.objects.get(id=tran_memo_text_id)
            memo_object.delete()
            validated_data["memo_text_id"] = None

    class Meta(ScheduleBTransactionSerializerBase.Meta):
        fields = [
            f.name
            for f in ScheduleBTransaction._meta.get_fields()
            if f.name not in ["deleted", "scheduleBtransaction"]
        ] + [
            "parent_transaction",
            "report_id",
            "contact_id",
            "memo_text_id",
            "children",
            "expenditure_aggregate",
            "itemized",
            "fields_to_validate",
        ]

        depth = 1
