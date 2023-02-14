from .models import F3XSummary
from rest_framework.serializers import (
    EmailField,
    CharField,
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
    report_status = CharField(
        read_only=True,
    )
    report_code_label = CharField(
        read_only=True,
    )

    class Meta:
        model = F3XSummary
        fields = [
            f.name
            for f in F3XSummary._meta.get_fields()
            if f.name
            not in [
                "deleted",
                "schatransaction",
                "scheduleatransaction",
                "schedulebtransaction",
                "transaction",
                "dotfec",
                "memotext",
                "uploadsubmission",
                "webprintsubmission",
            ]
        ] + ["report_status", "report_code_label"]
        read_only_fields = ["id", "deleted", "created", "updated"]
