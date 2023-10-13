from django.db import transaction
from fecfiler.reports.models import Report
from fecfiler.reports.report_f99.models import ReportF99
from fecfiler.reports.serializers import ReportSerializer
from fecfiler.shared.utilities import get_model_data
from rest_framework.serializers import CharField
import logging


logger = logging.getLogger(__name__)


class ReportF99Serializer(ReportSerializer):
    schema_name = "F99"

    street_1 = CharField(required=False, allow_null=True)
    street_2 = CharField(required=False, allow_null=True)
    city = CharField(required=False, allow_null=True)
    state = CharField(required=False, allow_null=True)
    zip = CharField(required=False, allow_null=True)
    text_code = CharField(required=False, allow_null=True)

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        report = ReportSerializer(context=self.context).to_internal_value(data)
        internal.update(report)
        return internal

    def create(self, validated_data: dict):
        with transaction.atomic():
            report_f99_data = get_model_data(validated_data, ReportF99)
            report_f99 = ReportF99.objects.create(**report_f99_data)
            report_data = get_model_data(validated_data, Report)
            report_data["report_f99_id"] = report_f99.id
            report = super().create(report_data)
            return report

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.schedule_a, attr, value)
            instance.report_f99.save()
            updated = super().update(instance, validated_data)
            return updated

    def validate(self, data):
        self.context["fields_to_ignore"] = self.context.get(
            "fields_to_ignore", ["filer_committee_id_number"]
        )
        return super().validate(data)

    class Meta(ReportSerializer.Meta):
        fields = (
            ReportSerializer.Meta.get_fields()
            + [
                f.name
                for f in ReportF99._meta.get_fields()
                if f.name not in ["committee_name", "report"]
            ]
            + ["fields_to_validate"]
        )

        read_only_fields = ["id"]
