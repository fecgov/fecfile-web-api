from .models import F3XSummary, ReportCodeLabel
from rest_framework.serializers import (
    ModelSerializer,
    SlugRelatedField,
    EmailField,
    SerializerMethodField
)
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.web_services.serializers import (
    UploadSubmissionSerializer,
    WebPrintSubmissionSerializer,
)
from fecfiler.validation.serializers import FecSchemaValidatorSerializerMixin
import logging

logger = logging.getLogger(__name__)


class F3XSummarySerializer(CommitteeOwnedSerializer, FecSchemaValidatorSerializerMixin):
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
    upload_submission = UploadSubmissionSerializer(
        read_only=True,
    )
    webprint_submission = WebPrintSubmissionSerializer(
        read_only=True,
    )

    submission_status = SerializerMethodField()

    def get_submission_status(self, obj):
        if hasattr(obj, "submission_status"):
            return obj.submission_status
        return None

    class Meta:
        model = F3XSummary
        fields = [
            f.name
            for f in F3XSummary._meta.get_fields()
            if f.name
            not in [
                "deleted",
                "schatransaction",
                "dotfec",
                "memotext",
                "uploadsubmission",
                "webprintsubmission",
            ]
        ] + ["submission_status"]
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
