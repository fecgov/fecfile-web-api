from django.db import transaction
from fecfiler.reports.models import Report
from fecfiler.reports.form_24.models import Form24
from fecfiler.reports.serializers import ReportSerializer
from fecfiler.shared.utilities import get_model_data
from rest_framework.serializers import (
    CharField,
    DateField,
)
import logging


logger = logging.getLogger(__name__)


class Form24Serializer(ReportSerializer):
    schema_name = "F24"

    report_type_24_48 = CharField(required=False, allow_null=True)
    original_amendment_date = DateField(required=False, allow_null=True)
    street_1 = CharField(required=False, allow_null=True)
    street_2 = CharField(required=False, allow_null=True)
    city = CharField(required=False, allow_null=True)
    state = CharField(required=False, allow_null=True)
    zip = CharField(required=False, allow_null=True)

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        report = ReportSerializer(context=self.context).to_internal_value(data)
        internal.update(report)
        return internal

    def create(self, validated_data: dict):
        with transaction.atomic():
            form_24_data = get_model_data(validated_data, Form24)
            form_24 = Form24.objects.create(**form_24_data)
            report_data = get_model_data(validated_data, Report)
            report_data["form_24_id"] = form_24.id
            report = super().create(report_data)
            return report

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.form_24, attr, value)
            instance.form_24.save()
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
                for f in Form24._meta.get_fields()
                if f.name not in ["committee_name", "report"]
            ]
            + ["fields_to_validate"]
        )

        read_only_fields = ["id"]
