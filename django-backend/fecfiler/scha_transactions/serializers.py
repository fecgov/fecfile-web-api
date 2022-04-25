from .models import SchATransaction
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.validation import serializers
from functools import reduce
import logging

logger = logging.getLogger(__name__)


class SchATransactionSerializer(
    CommitteeOwnedSerializer, serializers.FecSchemaValidatorSerializer
):
    schema_name = "SchA"

    class Meta:
        model = SchATransaction
        fields = [
            f.name for f in SchATransaction._meta.get_fields() if f.name != "deleted"
        ]
        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
