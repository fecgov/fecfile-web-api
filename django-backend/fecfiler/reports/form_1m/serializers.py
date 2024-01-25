from django.db import transaction
from fecfiler.reports.models import Report
from fecfiler.reports.form_1m.models import Form1M
from fecfiler.reports.serializers import ReportSerializer
from fecfiler.contacts.serializers import ContactSerializer, create_or_update_contact
from fecfiler.contacts.models import Contact
from fecfiler.shared.utilities import get_model_data
from rest_framework.serializers import CharField, DateField, UUIDField
import logging


logger = logging.getLogger(__name__)

CONTACT_FIELDS = [
    'affiliated_committee_fec_id',
    'affiliated_committee_name',
    'I_candidate_id_number',
    'I_candidate_last_name',
    'I_candidate_first_name',
    'I_candidate_middle_name',
    'I_candidate_prefix',
    'I_candidate_suffix',
    'I_candidate_office',
    'I_candidate_district',
    'I_candidate_state',
    'II_candidate_id_number',
    'II_candidate_last_name',
    'II_candidate_first_name',
    'II_candidate_middle_name',
    'II_candidate_prefix',
    'II_candidate_suffix',
    'II_candidate_office',
    'II_candidate_district',
    'II_candidate_state',
    'III_candidate_id_number',
    'III_candidate_last_name',
    'III_candidate_first_name',
    'III_candidate_middle_name',
    'III_candidate_prefix',
    'III_candidate_suffix',
    'III_candidate_office',
    'III_candidate_district',
    'III_candidate_state',
    'IV_candidate_id_number',
    'IV_candidate_last_name',
    'IV_candidate_first_name',
    'IV_candidate_middle_name',
    'IV_candidate_prefix',
    'IV_candidate_suffix',
    'IV_candidate_office',
    'IV_candidate_district',
    'IV_candidate_state',
    'V_candidate_id_number',
    'V_candidate_last_name',
    'V_candidate_first_name',
    'V_candidate_middle_name',
    'V_candidate_prefix',
    'V_candidate_suffix',
    'V_candidate_office',
    'V_candidate_district',
    'V_candidate_state',
]

CONTACT_KEYS = [
    'contact_affiliated',
    'contact_candidate_I',
    'contact_candidate_II',
    'contact_candidate_III',
    'contact_candidate_IV',
    'contact_candidate_V',
]


class Form1MSerializer(ReportSerializer):
    schema_name = "F1M"

    committee_name = CharField(required=False, allow_null=True)
    street_1 = CharField(required=False, allow_null=True)
    street_2 = CharField(required=False, allow_null=True)
    city = CharField(required=False, allow_null=True)
    state = CharField(required=False, allow_null=True)
    zip = CharField(required=False, allow_null=True)
    committee_type = CharField(required=False, allow_null=True)

    contact_affiliated = ContactSerializer(required=False, allow_null=True)
    contact_affiliated_id = UUIDField(required=False, allow_null=True)
    contact_candidate_I = ContactSerializer(required=False, allow_null=True)  # noqa: N815
    contact_candidate_I_id = UUIDField(required=False, allow_null=True)  # noqa: N815
    contact_candidate_II = ContactSerializer(required=False, allow_null=True)  # noqa: N815,E501
    contact_candidate_II_id = UUIDField(required=False, allow_null=True)  # noqa: N815
    contact_candidate_III = ContactSerializer(required=False, allow_null=True)  # noqa: N815,E501
    contact_candidate_III_id = UUIDField(required=False, allow_null=True)  # noqa: N815
    contact_candidate_IV = ContactSerializer(required=False, allow_null=True)  # noqa: N815,E501
    contact_candidate_IV_id = UUIDField(required=False, allow_null=True)  # noqa: N815
    contact_candidate_V = ContactSerializer(required=False, allow_null=True)  # noqa: N815
    contact_candidate_V_id = UUIDField(required=False, allow_null=True)  # noqa: N815

    affiliated_date_form_f1_filed = DateField(required=False, allow_null=True)
    affiliated_committee_fec_id = CharField(required=False, allow_null=True)
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

    date_of_original_registration = DateField(required=False, allow_null=True)
    date_of_51st_contributor = DateField(required=False, allow_null=True)
    date_committee_met_requirements = DateField(required=False, allow_null=True)

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        report = ReportSerializer(context=self.context).to_internal_value(data)
        internal.update(report)
        return internal

    def create(self, validated_data: dict):
        with transaction.atomic():
            self.write_contacts(validated_data)
            form_1m_data = get_model_data(validated_data, Form1M)
            form_1m = Form1M.objects.create(**form_1m_data)
            report_data = get_model_data(validated_data, Report)
            report_data["form_1m_id"] = form_1m.id
            return super().create(report_data)

    def update(self, instance, validated_data: dict):
        with transaction.atomic():
            self.write_contacts(validated_data)
            for attr, value in validated_data.items():
                if attr != "id":
                    setattr(instance.form_1m, attr, value)
            instance.form_1m.save()
            return super().update(instance, validated_data)

    def write_contacts(self, validated_data: dict):
        for contact_key in CONTACT_KEYS:
            create_or_update_contact(validated_data, contact_key)

    def validate(self, data):
        self.context["fields_to_ignore"] = self.context.get(
            "fields_to_ignore", ["filer_committee_id_number"]
        )
        return super().validate(data)

    class Meta(ReportSerializer.Meta):
        fields = (
            ReportSerializer.Meta.get_fields()
            + [f.name for f in Form1M._meta.get_fields() if f.name not in ["report"]]
            + CONTACT_FIELDS
            + [
                "fields_to_validate",
                "contact_affiliated_id",
                "contact_candidate_I_id",
                "contact_candidate_II_id",
                "contact_candidate_III_id",
                "contact_candidate_IV_id",
                "contact_candidate_V_id",
            ]
        )

        read_only_fields = ["id"]
