from fecfiler.f3x_summaries.models import F3XSummary
from .models import SchATransaction
from rest_framework.serializers import PrimaryKeyRelatedField
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.validation import serializers
from rest_framework.serializers import PrimaryKeyRelatedField
import logging

logger = logging.getLogger(__name__)


class SchATransactionSerializer(
    CommitteeOwnedSerializer, serializers.FecSchemaValidatorSerializerMixin
):
    schema_name = "SchA"
    parent_transaction_id = PrimaryKeyRelatedField(
        default=None,
        many=False,
        required=False,
        allow_null=True,
        queryset=SchATransaction.objects.all(),
    )

    report_id = PrimaryKeyRelatedField(
        many=False,
        required=True,
        allow_null=False,
        queryset=F3XSummary.objects.all()
    )

    class Meta:
        model = SchATransaction
        fields = [
            f.name for f in SchATransaction._meta.get_fields() if f.name not in [
                "deleted",
                "schatransaction"
            ]
        ]

        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
