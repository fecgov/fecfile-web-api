import logging

from django.db import transaction
from fecfiler.transactions.serializers import TransactionSerializerBase
from rest_framework.serializers import DecimalField, ListSerializer
from fecfiler.f3x_summaries.serializers import F3XSummarySerializer


from fecfiler.transactions.schedule_b.models import ScheduleBTransaction

logger = logging.getLogger(__name__)


class ScheduleBTransactionSerializerBase(TransactionSerializerBase):

    """These fields are generated in the query"""

    report = F3XSummarySerializer(read_only=True)

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
    report = F3XSummarySerializer(read_only=True)

    parent_transaction = ScheduleBTransactionSerializerBase(
        allow_null=True, required=False, read_only="True"
    )

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        # Add child transactions to transaction.children field in JSON output
        existing_children = ScheduleBTransaction.objects.filter(
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

    def update(self, instance: ScheduleBTransaction, validated_data: dict):
        with transaction.atomic():
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
