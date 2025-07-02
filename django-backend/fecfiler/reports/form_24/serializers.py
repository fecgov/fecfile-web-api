from django.db import transaction
from fecfiler.reports.models import Report
from fecfiler.reports.form_24.models import Form24
from fecfiler.reports.serializers import ReportSerializer
from fecfiler.shared.utilities import get_model_data
from rest_framework.serializers import CharField, DateField
from rest_framework.exceptions import ValidationError
import structlog

logger = structlog.get_logger(__name__)


class Form24Serializer(ReportSerializer):
    schema_name = "F24"

    report_type_24_48 = CharField(required=False, allow_null=True)
    original_amendment_date = DateField(required=False, allow_null=True)
    name = CharField(required=False, allow_null=True)

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
        self._context = self.context.copy()
        self._context["fields_to_ignore"] = self._context.get(
            "fields_to_ignore", ["filer_committee_id_number"]
        )
        request = self.context.get("request", None)

        committee_account = request.data.get("committee_account")
        if committee_account is None:
            raise ValidationError("Committee account context is required.")
        form_24_name = data.get("name")
        form_24_id = self.instance.form_24.id if self.instance else None

        name_used = Form24.objects.filter(
            name=form_24_name, report__committee_account=committee_account
        )

        if form_24_id:
            name_used = name_used.exclude(id=form_24_id)

        if name_used.exists():
            raise ValidationError(
                {
                    "name": (
                        f'A Form 24 with name "{form_24_name}"',
                        "already exists for this committee.",
                    )
                }
            )

        return super().validate(data)

    class Meta(ReportSerializer.Meta):
        fields = (
            ReportSerializer.Meta.get_fields()
            + [f.name for f in Form24._meta.get_fields() if f.name not in ["report"]]
            + ["fields_to_validate"]
        )

        read_only_fields = ["id"]
