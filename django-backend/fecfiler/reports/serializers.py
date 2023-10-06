from .models import Report
from rest_framework.serializers import ModelSerializer, CharField, UUIDField
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.web_services.serializers import (
    UploadSubmissionSerializer,
    WebPrintSubmissionSerializer,
)
from fecfiler.validation.serializers import FecSchemaValidatorSerializerMixin
from fecfiler.repports.report_f3x.models import ReportF3X
import logging


logger = logging.getLogger(__name__)


class ReportF3XSerializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in ReportF3X._meta.get_fields()
            if f.name not in ["deleted", "report"]
        ]
        model = ReportF3X


class ReportSerializer(CommitteeOwnedSerializer, FecSchemaValidatorSerializerMixin):
    id = UUIDField(required=False)
    upload_submission = UploadSubmissionSerializer(read_only=True,)
    webprint_submission = WebPrintSubmissionSerializer(read_only=True,)
    report_status = CharField(read_only=True,)
    report_code_label = CharField(read_only=True,)

    report_f3x = ReportF3XSerializer(required=False)

    def validate(self, data):
        self.context["fields_to_ignore"] = self.context.get(
            "fields_to_ignore", ["filer_committee_id_number"]
        )
        return super().validate(data)

    class Meta:
        model = Report
        fields = [
            f.name
            for f in Report._meta.get_fields()
            if f.name
            not in ["deleted", "dotfec", "uploadsubmission", "webprintsubmission",]
        ] + ["report_status", "report_code_label", "fields_to_validate"]
        read_only_fields = ["id", "deleted", "created", "updated"]
