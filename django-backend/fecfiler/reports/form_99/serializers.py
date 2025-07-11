from django.db import transaction
from fecfiler.reports.models import Report
from fecfiler.reports.form_99.models import Form99
from fecfiler.reports.serializers import ReportSerializer
from fecfiler.shared.utilities import get_model_data
from rest_framework.serializers import CharField, BooleanField
import structlog

logger = structlog.get_logger(__name__)


class Form99Serializer(ReportSerializer):
    schema_name = "F99"

    text_code = CharField(required=False, allow_null=True)
    filing_frequency = CharField(required=False, allow_null=True)
    pdf_attachment = BooleanField(required=False, allow_null=True)
    message_text = CharField(required=False, allow_null=True)

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        report = ReportSerializer(context=self.context).to_internal_value(data)
        internal.update(report)
        return internal

    def create(self, validated_data: dict):
        with transaction.atomic():
            form_99_data = get_model_data(validated_data, Form99)
            form_99 = Form99.objects.create(**form_99_data)
            report_data = get_model_data(validated_data, Report)
            report_data["form_99_id"] = form_99.id
            report = super().create(report_data)
            return report

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.form_99, attr, value)
            instance.form_99.save()
            updated = super().update(instance, validated_data)
            return updated

    def validate(self, data):
        self._context = self.context.copy()
        self._context["fields_to_ignore"] = self._context.get(
            "fields_to_ignore", ["filer_committee_id_number"]
        )
        return super().validate(data)

    class Meta(ReportSerializer.Meta):
        fields = (
            ReportSerializer.Meta.get_fields()
            + [f.name for f in Form99._meta.get_fields() if f.name not in ["report"]]
            + ["fields_to_validate"]
        )

        read_only_fields = ["id"]
