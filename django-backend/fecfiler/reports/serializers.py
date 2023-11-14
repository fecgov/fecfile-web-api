from .models import Report
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
    UUIDField,
)
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.web_services.serializers import (
    UploadSubmissionSerializer,
    WebPrintSubmissionSerializer,
)
from fecfiler.validation.serializers import FecSchemaValidatorSerializerMixin
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.reports.form_24.models import Form24
from fecfiler.reports.form_99.models import Form99
import logging


logger = logging.getLogger(__name__)


class Form3XSerializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in Form3X._meta.get_fields()
            if f.name not in ["deleted", "report"]
        ]
        model = Form3X


class Form24Serializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in Form24._meta.get_fields()
            if f.name not in ["deleted", "report"]
        ]
        model = Form24


class Form99Serializer(ModelSerializer):
    class Meta:
        fields = [
            f.name
            for f in Form99._meta.get_fields()
            if f.name not in ["deleted", "report"]
        ]
        model = Form99


class ReportSerializer(CommitteeOwnedSerializer, FecSchemaValidatorSerializerMixin):
    id = UUIDField(required=False)

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

    form_3x = Form3XSerializer(required=False)
    form_24 = Form24Serializer(required=False)
    form_99 = Form99Serializer(required=False)

    def to_representation(self, instance, depth=0):
        representation = super().to_representation(instance)
        form_3x = representation.pop("form_3x") or []
        form_24 = representation.pop("form_24") or []
        form_99 = representation.pop("form_99") or []

        if form_3x:
            representation["report_type"] = "F3X"
            for property in form_3x:
                if not representation.get(property):
                    representation[property] = form_3x[property]
        if form_24:
            representation["report_type"] = "F24"
            for property in form_24:
                if not representation.get(property):
                    representation[property] = form_24[property]
        if form_99:
            representation["report_type"] = "F99"
            for property in form_99:
                if not representation.get(property):
                    representation[property] = form_99[property]
        return representation

    def validate(self, data):
        self._context = self.context.copy()
        self._context["fields_to_ignore"] = self._context.get(
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
