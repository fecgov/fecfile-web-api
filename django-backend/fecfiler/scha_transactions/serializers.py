from .models import SchATransaction
from rest_framework.serializers import PrimaryKeyRelatedField
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.validation import serializers
import logging

logger = logging.getLogger(__name__)


class SchATransactionSerializer(
    CommitteeOwnedSerializer, serializers.FecSchemaValidatorSerializerMixin
):
    schema_name = "SchA"
    parent_transaction = PrimaryKeyRelatedField(
        many=False,
        required=False,
        queryset=SchATransaction.objects.all(),
    )

    class Meta:
        model = SchATransaction
        fields = [
            f.name for f in SchATransaction._meta.get_fields() if f.name not in ["deleted", "schatransaction"]
        ]
        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
