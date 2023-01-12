import logging

from django.db import transaction
from fecfiler.transactions.serializers import TransactionSerializerBase
from rest_framework.serializers import DecimalField, ListSerializer
from fecfiler.f3x_summaries.serializers import F3XSummarySerializer


from fecfiler.transactions.schedule_a.models import ScheduleATransaction

logger = logging.getLogger(__name__)


class ScheduleATransactionSerializerBase(TransactionSerializerBase):

    """These fields are generated in the query"""

    report = F3XSummarySerializer(read_only=True)

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

    report = F3XSummarySerializer(read_only=True)

    parent_transaction = ScheduleATransactionSerializerBase(
        allow_null=True, required=False, read_only="True"
    )

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        # Add child transactions to transaction.children field in JSON output
        existing_children = ScheduleATransaction.objects.filter(
            parent_transaction_object_id=instance.id
        ).all()
        ret["children"] = map(self.to_representation, existing_children)
        return ret

    def create(self, validated_data: dict):
        with transaction.atomic():
            children = validated_data.pop("children", [])
            parent = super().create(validated_data)
            for child in children:
                child["parent_transaction_object_id"] = parent.id
                self.create(child)
            return parent

    def update(self, instance: ScheduleATransaction, validated_data: dict):
        with transaction.atomic():
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
