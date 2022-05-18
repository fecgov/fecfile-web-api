from .models import F3XSummary
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.validation import serializers
import logging

logger = logging.getLogger(__name__)


class F3XSummarySerializer(
    CommitteeOwnedSerializer, serializers.FecSchemaValidatorSerializerMixin
):
    schema_name = "F3X"

    class Meta:
        model = F3XSummary
        fields = [f.name for f in F3XSummary._meta.get_fields() if f.name not in ["deleted", "schatransaction"]]
        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
