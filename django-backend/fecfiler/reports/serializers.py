from .models import Report
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
    UUIDField,
    EmailField,
)
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.web_services.serializers import (
    UploadSubmissionSerializer,
    WebPrintSubmissionSerializer,
)
from fecfiler.validation.serializers import FecSchemaValidatorSerializerMixin
from fecfiler.reports.report_f3x.models import ReportF3X
from fecfiler.reports.report_f24.models import ReportF24
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


class ReportF24Serializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in ReportF24._meta.get_fields()
            if f.name not in ["deleted", "report"]
        ]
        model = ReportF24


class ReportSerializer(CommitteeOwnedSerializer, FecSchemaValidatorSerializerMixin):
    id = UUIDField(required=False)

    upload_submission = UploadSubmissionSerializer(read_only=True,)
    webprint_submission = WebPrintSubmissionSerializer(read_only=True,)
    report_status = CharField(read_only=True,)
    report_code_label = CharField(read_only=True,)

    report_f3x = ReportF3XSerializer(required=False)
    report_f24 = ReportF24Serializer(required=False)

    def to_representation(self, instance, depth=0):
        representation = super().to_representation(instance)
        report_f3x = representation.pop("report_f3x") or []
        report_f24 = representation.pop("report_f24") or []

        if report_f3x:
            representation["report_type"] = "F3X"
            for property in report_f3x:
                if not representation.get(property):
                    representation[property] = report_f3x[property]
        if report_f24:
            representation["report_type"] = "F24"
            for property in report_f24:
                if not representation.get(property):
                    representation[property] = report_f24[property]
        return representation

    def validate(self, data):
        self.context["fields_to_ignore"] = self.context.get(
            "fields_to_ignore", ["filer_committee_id_number"]
        )
        return super().validate(data)

    class Meta:
        model = Report

        def get_fields():
            return [
                f.name
                for f in Report._meta.get_fields()
                if f.name
                not in [
                    "deleted",
                    "uploadsubmission",
                    "webprintsubmission",
                    "committee_name",
                    "memotext",
                    "transaction",
                    "dotfec",
                    "report",
                ]
            ] + ["report_status", "fields_to_validate", "report_code_label"]

        fields = get_fields()
        read_only_fields = ["id", "deleted", "created", "updated"]
