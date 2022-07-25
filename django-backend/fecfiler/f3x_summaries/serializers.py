from .models import F3XSummary, ReportCodeLabel
from rest_framework.serializers import ModelSerializer, SlugRelatedField, EmailField
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.validation import serializers
import logging

logger = logging.getLogger(__name__)


class F3XSummarySerializer(
    CommitteeOwnedSerializer, serializers.FecSchemaValidatorSerializerMixin
):
    schema_name = "F3X"
    report_code = SlugRelatedField(
        many=False,
        required=False,
        read_only=False,
        slug_field="report_code",
        queryset=ReportCodeLabel.objects.all(),
    )
    confirmation_email_1 = EmailField(
        max_length=44,
        min_length=None,
        allow_blank=True,
        allow_null=True,
        required=False,
    )
    confirmation_email_2 = EmailField(
        max_length=44,
        min_length=None,
        allow_blank=True,
        allow_null=True,
        required=False,
    )

    class Meta:
        model = F3XSummary
        fields = [
            f.name
            for f in F3XSummary._meta.get_fields()
            if f.name not in ["deleted", "schatransaction", "dotfec"]
        ]
        read_only_fields = [
            "id",
            "deleted",
            "created",
            "updated",
        ]
        foreign_key_fields = {"report_code": "report_code"}


class ReportCodeLabelSerializer(ModelSerializer):
    class Meta:
        model = ReportCodeLabel
        fields = ("label", "report_code")
