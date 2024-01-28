from rest_framework.serializers import (
    CharField,
    ModelSerializer,
)
from fecfiler.transactions.schedule_e.models import ScheduleE
from fecfiler.shared.utilities import get_model_data


CONTACT_FIELDS = [
    'payee_organization_name',
    'payee_last_name',
    'payee_first_name',
    'payee_middle_name',
    'payee_prefix',
    'payee_suffix',
    'payee_street_1',
    'payee_street_2',
    'payee_city',
    'payee_state',
    'payee_zip',
    'so_candidate_id_number',
    'so_candidate_last_name',
    'so_candidate_first_name',
    'so_candidate_middle_name',
    'so_candidate_prefix',
    'so_candidate_suffix',
    'so_candidate_office',
    'so_candidate_district',
    'so_candidate_state',
]

def add_schedule_e_contact_fields(instance, representation):
    if instance.contact_1:
        representation['payee_organization_name'] = instance.contact_1.name
        representation['payee_last_name'] = instance.contact_1.last_name
        representation['payee_first_name'] = instance.contact_1.first_name
        representation['payee_middle_name'] = instance.contact_1.middle_name
        representation['payee_prefix'] = instance.contact_1.prefix
        representation['payee_suffix'] = instance.contact_1.suffix
        representation['payee_street_1'] = instance.contact_1.street_1
        representation['payee_street_2'] = instance.contact_1.street_2
        representation['payee_city'] = instance.contact_1.city
        representation['payee_state'] = instance.contact_1.state
        representation['payee_zip'] = instance.contact_1.zip
    if instance.contact_2:
        representation['so_candidate_id_number'] = instance.contact_2.candidate_id
        representation['so_candidate_last_name'] = instance.contact_2.last_name
        representation['so_candidate_first_name'] = instance.contact_2.first_name
        representation['so_candidate_middle_name'] = instance.contact_2.middle_name
        representation['so_candidate_prefix'] = instance.contact_2.prefix
        representation['so_candidate_suffix'] = instance.contact_2.suffix
        representation['so_candidate_office'] = instance.contact_2.candidate_office
        representation['so_candidate_district'] = instance.contact_2.candidate_district
        representation['so_candidate_state'] = instance.contact_2.candidate_state


class ScheduleESerializer(ModelSerializer):
    payee_organization_name = CharField(required=False, allow_null=True)
    payee_last_name = CharField(required=False, allow_null=True)
    payee_first_name = CharField(required=False, allow_null=True)
    payee_middle_name = CharField(required=False, allow_null=True)
    payee_prefix = CharField(required=False, allow_null=True)
    payee_suffix = CharField(required=False, allow_null=True)
    payee_street_1 = CharField(required=False, allow_null=True)
    payee_street_2 = CharField(required=False, allow_null=True)
    payee_city = CharField(required=False, allow_null=True)
    payee_state = CharField(required=False, allow_null=True)
    payee_zip = CharField(required=False, allow_null=True)
    so_candidate_id_number = CharField(required=False, allow_null=True)
    so_candidate_last_name = CharField(required=False, allow_null=True)
    so_candidate_first_name = CharField(required=False, allow_null=True)
    so_candidate_middle_name = CharField(required=False, allow_null=True)
    so_candidate_prefix = CharField(required=False, allow_null=True)
    so_candidate_suffix = CharField(required=False, allow_null=True)
    so_candidate_office = CharField(required=False, allow_null=True)
    so_candidate_district = CharField(required=False, allow_null=True)
    so_candidate_state = CharField(required=False, allow_null=True)

    def create(self, validated_data):
        model_data = get_model_data(validated_data, ScheduleE)
        return ScheduleE.objects.create(**model_data)

    class Meta:
        fields = [
            f.name
            for f in ScheduleE._meta.get_fields()
            if f.name not in ["transaction"]
        ] + CONTACT_FIELDS
        model = ScheduleE