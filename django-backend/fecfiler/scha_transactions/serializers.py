from .models import SchATransaction
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.validation import serializers
from rest_framework.serializers import CharField, UUIDField
from rest_framework.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)


class SchATransactionSerializer(
    CommitteeOwnedSerializer, serializers.FecSchemaValidatorSerializerMixin
):
    parent_transaction_id = UUIDField(required=False, allow_null=True)
    transaction_id = CharField(
        required=True, max_length=20, allow_blank=False, allow_null=True
    )

    report_id = UUIDField(required=True, allow_null=False)

    def get_schema_name(self, data):
        transaction_type = data.get("transaction_type_identifier", None)
        if not transaction_type:
            raise ValidationError(
                {
                    "transaction_type_identifier": [
                        "No transaction_type_identifier provided"
                    ]
                }
            )
        return transaction_type

    class Meta:
        model = SchATransaction
        fields = [
            f.name
            for f in SchATransaction._meta.get_fields()
            if f.name not in ["deleted", "schatransaction"]
        ] + ["parent_transaction_id", "report_id"]

        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
