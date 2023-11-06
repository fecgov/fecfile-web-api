from django.db import transaction
from fecfiler.reports.models import Report
from fecfiler.reports.form_1m.models import Form1M
from fecfiler.reports.serializers import ReportSerializer
from fecfiler.shared.utilities import get_model_data
from rest_framework.serializers import CharField, DateField, BooleanField
import logging


logger = logging.getLogger(__name__)


class Form1MSerializer(ReportSerializer):
    schema_name = "F1M"

    street_1 = CharField(required=False, allow_null=True)
    street_2 = CharField(required=False, allow_null=True)
    city = CharField(required=False, allow_null=True)
    state = CharField(required=False, allow_null=True)
    zip = CharField(required=False, allow_null=True)
    committee_type = CharField(required=False, allow_null=True)

    affiliated_date_form_f1_filed = DateField(required=False, allow_null=True)
    affiliated_date_committee_fec_id = DateField(required=False, allow_null=True)
    affiliated_committee_name = CharField(required=False, allow_null=True)

    I_candidate_id_number = CharField(required=False, allow_null=True)
    I_candidate_last_name = CharField(required=False, allow_null=True)
    I_candidate_first_name = CharField(required=False, allow_null=True)
    I_candidate_middle_name = CharField(required=False, allow_null=True)
    I_candidate_prefix = CharField(required=False, allow_null=True)
    I_candidate_suffix = CharField(required=False, allow_null=True)
    I_candidate_office = CharField(required=False, allow_null=True)
    I_candidate_state = CharField(required=False, allow_null=True)
    I_candidate_district = CharField(required=False, allow_null=True)
    I_date_of_contribution = DateField(required=False, allow_null=True)

    II_candidate_id_number = CharField(required=False, allow_null=True)
    II_candidate_last_name = CharField(required=False, allow_null=True)
    II_candidate_first_name = CharField(required=False, allow_null=True)
    II_candidate_middle_name = CharField(required=False, allow_null=True)
    II_candidate_prefix = CharField(required=False, allow_null=True)
    II_candidate_suffix = CharField(required=False, allow_null=True)
    II_candidate_office = CharField(required=False, allow_null=True)
    II_candidate_state = CharField(required=False, allow_null=True)
    II_candidate_district = CharField(required=False, allow_null=True)
    II_date_of_contribution = DateField(required=False, allow_null=True)

    III_candidate_id_number = CharField(required=False, allow_null=True)
    III_candidate_last_name = CharField(required=False, allow_null=True)
    III_candidate_first_name = CharField(required=False, allow_null=True)
    III_candidate_middle_name = CharField(required=False, allow_null=True)
    III_candidate_prefix = CharField(required=False, allow_null=True)
    III_candidate_suffix = CharField(required=False, allow_null=True)
    III_candidate_office = CharField(required=False, allow_null=True)
    III_candidate_state = CharField(required=False, allow_null=True)
    III_candidate_district = CharField(required=False, allow_null=True)
    III_date_of_contribution = DateField(required=False, allow_null=True)

    IV_candidate_id_number = CharField(required=False, allow_null=True)
    IV_candidate_last_name = CharField(required=False, allow_null=True)
    IV_candidate_first_name = CharField(required=False, allow_null=True)
    IV_candidate_middle_name = CharField(required=False, allow_null=True)
    IV_candidate_prefix = CharField(required=False, allow_null=True)
    IV_candidate_suffix = CharField(required=False, allow_null=True)
    IV_candidate_office = CharField(required=False, allow_null=True)
    IV_candidate_state = CharField(required=False, allow_null=True)
    IV_candidate_district = CharField(required=False, allow_null=True)
    IV_date_of_contribution = DateField(required=False, allow_null=True)

    V_candidate_id_number = CharField(required=False, allow_null=True)
    V_candidate_last_name = CharField(required=False, allow_null=True)
    V_candidate_first_name = CharField(required=False, allow_null=True)
    V_candidate_middle_name = CharField(required=False, allow_null=True)
    V_candidate_prefix = CharField(required=False, allow_null=True)
    V_candidate_suffix = CharField(required=False, allow_null=True)
    V_candidate_office = CharField(required=False, allow_null=True)
    V_candidate_state = CharField(required=False, allow_null=True)
    V_candidate_district = CharField(required=False, allow_null=True)
    V_date_of_contribution = DateField(required=False, allow_null=True)

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        report = ReportSerializer(context=self.context).to_internal_value(data)
        internal.update(report)
        return internal

    def create(self, validated_data: dict):
        with transaction.atomic():
            form_1m_data = get_model_data(validated_data, Form1M)
            form_1m = Form1M.objects.create(**form_99_data)
            report_data = get_model_data(validated_data, Report)
            report_data["form_1m_id"] = form_99.id
            report = super().create(report_data)
            return report

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.form_1m, attr, value)
            instance.form_1m.save()
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
                for f in Form1M._meta.get_fields()
                if f.name not in ["committee_name", "report"]
            ]
            + ["fields_to_validate"]
        )

        read_only_fields = ["id"]
