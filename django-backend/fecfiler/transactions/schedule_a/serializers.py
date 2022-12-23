import logging

from django.db import transaction
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


from fecfiler.transactions.schedule_a.models import ScheduleATransaction

logger = logging.getLogger(__name__)


class ScheduleATransactionSerializerBase(TransactionSerializerBase):

    """These fields are generated in the query"""

    contribution_aggregate = DecimalField(
        max_digits=11, decimal_places=2, read_only=True
    )

    def validate(self, attrs):
        """Adds stub contribution_aggregate to pass validation"""
        attrs["contribution_aggregate"] = 0
        data = super().validate(attrs)
        del data["contribution_aggregate"]
        return data

    class Meta:
        model = ScheduleATransaction
        fields = [
            f.name
            for f in ScheduleATransaction._meta.get_fields()
            if f.name not in ["deleted", "scheduleatransaction"]
        ] + [
            "report_id",
            "contact_id",
            "memo_text_id",
            "contribution_aggregate",
            "itemized",
            "fields_to_validate",
        ]


class ScheduleATransactionSerializer(ScheduleATransactionSerializerBase):
    children = ListSerializer(
        child=ScheduleATransactionSerializerBase(),
        allow_null=True,
        allow_empty=True,
        required=False,
    )

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        # Add child transactions to transaction.children field in JSON output
        existing_children = ScheduleATransaction.objects.filter(
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
            self.create_or_update_memo_text(validated_data)
            children = validated_data.pop("children", [])
            parent = super().create(validated_data)
            for child in children:
                child["parent_transaction_object_id"] = parent.id
                self.create(child)
            return parent

    def update(self, instance: ScheduleATransaction, validated_data: dict):
        with transaction.atomic():
            self.create_or_update_memo_text(validated_data)
            children = validated_data.pop("children", [])

            existing_children = ScheduleATransaction.objects.filter(
                parent_transaction_object_id=instance.id
            ).all()
            for child in children:
                try:
                    """this will not make multiple db calls because
                    the existing_children queryset is cached
                    """
                    existing_child = existing_children.get(id=child.get("id", None))
                    self.update(existing_child, child)
                except ScheduleATransaction.DoesNotExist:
                    self.create(child)
            return super().update(instance, validated_data)

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

    class Meta(ScheduleATransactionSerializerBase.Meta):
        fields = [
            f.name
            for f in ScheduleATransaction._meta.get_fields()
            if f.name not in ["deleted", "scheduleatransaction"]
        ] + [
            "parent_transaction",
            "report_id",
            "contact_id",
            "memo_text_id",
            "children",
            "contribution_aggregate",
            "itemized",
            "fields_to_validate",
        ]

        depth = 1
