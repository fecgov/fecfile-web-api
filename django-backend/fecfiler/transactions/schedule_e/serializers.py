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
