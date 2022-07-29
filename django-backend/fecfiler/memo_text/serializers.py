from .models import MemoText
from fecfiler.validation import serializers
from rest_framework.serializers import ModelSerializer, IntegerField
import logging

logger = logging.getLogger(__name__)


class MemoTextSerializer(
    ModelSerializer, serializers.FecSchemaValidatorSerializerMixin
):
    schema_name = "Text"
    report_id = IntegerField(required=True, allow_null=False)

    class Meta:
        model = MemoText
        fields = [
            f.name for f in MemoText._meta.get_fields() if f.name not in ["report"]
        ] + ["report_id"]
