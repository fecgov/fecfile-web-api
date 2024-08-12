from .models import PDF, Report
from rest_framework.serializers import (
    ModelSerializer,
    CharField,
    UUIDField,
    BooleanField,
)
from fecfiler.committee_accounts.serializers import CommitteeOwnedSerializer
from fecfiler.web_services.serializers import (
    UploadSubmissionSerializer,
    WebPrintSubmissionSerializer,
)
from fecfiler.contacts.serializers import ContactSerializer
from fecfiler.validation.serializers import FecSchemaValidatorSerializerMixin
from fecfiler.reports.form_3x.models import Form3X
from fecfiler.reports.form_24.models import Form24
from fecfiler.reports.form_99.models import Form99
from fecfiler.reports.form_1m.models import Form1M
from fecfiler.reports.form_1m.utils import add_form_1m_contact_fields
import structlog

logger = structlog.get_logger(__name__)


class Form3XSerializer(ModelSerializer):
    class Meta:
        fields = [f.name for f in Form3X._meta.get_fields() if f.name not in ["report"]]
        model = Form3X


class Form24Serializer(ModelSerializer):
    class Meta:
        fields = [f.name for f in Form24._meta.get_fields() if f.name not in ["report"]]
        model = Form24


class Form99Serializer(ModelSerializer):
    class Meta:
        fields = [f.name for f in Form99._meta.get_fields() if f.name not in ["report"]]
        model = Form99


class Form1MSerializer(ModelSerializer):

    contact_affiliated_id = UUIDField(allow_null=True, required=False)
    contact_candidate_I_id = UUIDField(allow_null=True, required=False)  # noqa: N815
    contact_candidate_II_id = UUIDField(allow_null=True, required=False)  # noqa: N815
    contact_candidate_III_id = UUIDField(allow_null=True, required=False)  # noqa: N815
    contact_candidate_IV_id = UUIDField(allow_null=True, required=False)  # noqa: N815
    contact_candidate_V_id = UUIDField(allow_null=True, required=False)  # noqa: N815
    contact_affiliated = ContactSerializer(allow_null=True, required=False)

    contact_candidate_I = ContactSerializer(allow_null=True, required=False)  # noqa: N815
    contact_candidate_II = ContactSerializer(  # noqa: N815
        allow_null=True, required=False
    )
    contact_candidate_III = ContactSerializer(  # noqa: N815
        allow_null=True, required=False
    )
    contact_candidate_IV = ContactSerializer(  # noqa: N815
        allow_null=True, required=False
    )
    contact_candidate_V = ContactSerializer(allow_null=True, required=False)  # noqa: N815

    class Meta:
        fields = [
            f.name for f in Form1M._meta.get_fields() if f.name not in ["report"]
        ] + [
            "contact_affiliated_id",
            "contact_candidate_I_id",
            "contact_candidate_II_id",
            "contact_candidate_III_id",
            "contact_candidate_IV_id",
            "contact_candidate_V_id",
        ]
        model = Form1M


class ReportSerializer(CommitteeOwnedSerializer, FecSchemaValidatorSerializerMixin):
    id = UUIDField(required=False)

    committee_name = CharField(required=False, allow_null=True)
    street_1 = CharField(required=False, allow_null=True)
    street_2 = CharField(required=False, allow_null=True)
    city = CharField(required=False, allow_null=True)
    state = CharField(required=False, allow_null=True)
    zip = CharField(required=False, allow_null=True)

    upload_submission = UploadSubmissionSerializer(
        read_only=True,
    )
    webprint_submission = WebPrintSubmissionSerializer(
        read_only=True,
    )
    report_status = CharField(
        read_only=True,
    )
    report_code_label = CharField(read_only=True)
    version_label = CharField(read_only=True)
    is_first = BooleanField(read_only=True)

    form_3x = Form3XSerializer(required=False)
    form_24 = Form24Serializer(required=False)
    form_99 = Form99Serializer(required=False)
    form_1m = Form1MSerializer(required=False)

    def to_representation(self, instance: Report, depth=0):
        representation = super().to_representation(instance)
        form_3x = representation.pop("form_3x") or []
        form_24 = representation.pop("form_24") or []
        form_99 = representation.pop("form_99") or []
        form_1m = representation.pop("form_1m") or []
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
        if form_1m:
            representation["report_type"] = "F1M"
            add_form_1m_contact_fields(form_1m, representation)
            for property in form_1m:
                if not representation.get(property):
                    representation[property] = form_1m[property]

        if not representation.get("is_first"):
            this_report = Report.objects.get(id=representation["id"])
            representation["is_first"] = this_report.is_first if this_report else True

        representation["can_delete"] = instance.can_delete
        representation["can_unamend"] = instance.can_unamend

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
                    "uploadsubmission",
                    "webprintsubmission",
                    "memotext",
                    "transaction",
                    "transactions",
                    "dotfec",
                    "report",
                    "reporttransaction",
                ]
            ] + [
                "report_status",
                "fields_to_validate",
                "report_code_label",
                "version_label",
                "is_first",
            ]

        fields = get_fields()
        read_only_fields = ["id", "created", "updated", "is_first"]


class PDFSerializer(ModelSerializer):
    class Meta:
        model = PDF
        fields = "__all__"
