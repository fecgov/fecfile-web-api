from fecfiler.f3x_summaries.models import F3XSummary
from .models import MemoText
from fecfiler.validation import serializers
from rest_framework.serializers import ModelSerializer
from rest_framework.serializers import PrimaryKeyRelatedField
import logging

logger = logging.getLogger(__name__)


class MemoTextSerializer(
    ModelSerializer,
    serializers.FecSchemaValidatorSerializerMixin
):
    schema_name = "Text"
    report_id = PrimaryKeyRelatedField(
        many=False,
        required=True,
        allow_null=False,
        queryset=F3XSummary.objects.all()
    )

    class Meta:
        model = MemoText
        fields = [f.name for f in MemoText._meta.get_fields() if f.name not in [
        ]]
