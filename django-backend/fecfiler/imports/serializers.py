from .models import Imports
from fecfiler.validation import serializers
from rest_framework.serializers import UUIDField, ModelSerializer
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
import structlog

logger = structlog.get_logger(__name__)


class ImportsSerializer(
    CommitteeOwnedSerializer
):
    class Meta:
        model = Imports
        fields = [
            f.name
            for f in Imports._meta.get_fields()
            if f.name
            not in [
                "deleted",
                "dot_fec_file",
            ]
        ]
        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
            "dot_fec_file",
            "preprocessed_file",
            "report_type",
            "status"
        ]
