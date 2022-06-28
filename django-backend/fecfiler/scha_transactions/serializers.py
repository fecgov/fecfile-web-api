from .models import SchATransaction
from rest_framework.serializers import PrimaryKeyRelatedField, CharField
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

    ##Annotated Fields
    parent_organization_name = CharField(
        allow_blank = True,
        required = False,
    )

    class Meta:
        model = SchATransaction
        annotated_fields = ["parent_organization_name"]
        fields = [
            f.name for f in SchATransaction._meta.get_fields() if f.name not in [
                "deleted",
                "schatransaction"
            ]
        ] + annotated_fields
        
        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
