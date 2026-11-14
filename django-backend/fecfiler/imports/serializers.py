from .models import Import
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from rest_framework.serializers import (
    PrimaryKeyRelatedField,
    UUIDField,
    CharField,
    FileField,
    ValidationError,
    ModelSerializer,
    Serializer,
)
import structlog

logger = structlog.getLogger(__name__)


class ImportSerializer(ModelSerializer):
    id = UUIDField(read_only=True)
    status = CharField(read_only=True)

    class Meta:
        model = Import
        fields = ["id", "status"]


class ImportUploadSerializer(Serializer):
    file = FileField()
