from rest_framework.serializers import (
    CharField,
    ModelSerializer,
)
from fecfiler.transactions.schedule_c.models import ScheduleC
from fecfiler.shared.utilities import get_model_data


CONTACT_FIELDS = [
    'lender_organization_name',
    'lender_last_name',
    'lender_first_name',
    'lender_middle_name',
    'lender_prefix',
    'lender_suffix',
    'lender_street_1',
    'lender_street_2',
    'lender_city',
    'lender_state',
    'lender_zip',
    'lender_committee_id_number',
    'lender_candidate_id_number',
    'lender_candidate_first_name',
    'lender_candidate_last_name',
    'lender_candidate_middle_name',
    'lender_candidate_prefix',
    'lender_candidate_suffix',
    'lender_candidate_office',
    'lender_candidate_state',
    'lender_candidate_district',
]


def add_schedule_c_contact_fields(instance, representation):
    if instance.contact_1:
        representation['lender_organization_name'] = instance.contact_1.name
        representation['lender_last_name'] = instance.contact_1.last_name
        representation['lender_first_name'] = instance.contact_1.first_name
        representation['lender_middle_name'] = instance.contact_1.middle_name
        representation['lender_prefix'] = instance.contact_1.prefix
        representation['lender_suffix'] = instance.contact_1.suffix
        representation['lender_street_1'] = instance.contact_1.street_1
        representation['lender_street_2'] = instance.contact_1.street_2
        representation['lender_city'] = instance.contact_1.city
        representation['lender_state'] = instance.contact_1.state
        representation['lender_zip'] = instance.contact_1.zip
        representation['lender_committee_id_number'] = instance.contact_1.committee_id
    if instance.contact_2:
        representation['lender_candidate_id_number'] = instance.contact_2.candidate_id
        representation['lender_candidate_first_name'] = instance.contact_2.first_name
        representation['lender_candidate_last_name'] = instance.contact_2.last_name
        representation['lender_candidate_middle_name'] = instance.contact_2.middle_name
        representation['lender_candidate_prefix'] = instance.contact_2.prefix
        representation['lender_candidate_suffix'] = instance.contact_2.suffix
        representation['lender_candidate_office'] = instance.contact_2.candidate_office
        representation['lender_candidate_state'] = instance.contact_2.candidate_state
        representation['lender_candidate_district'] = (
            instance.contact_2.candidate_district
        )


class ScheduleCSerializer(ModelSerializer):
    lender_organization_name = CharField(required=False, allow_null=True)
    lender_last_name = CharField(required=False, allow_null=True)
    lender_first_name = CharField(required=False, allow_null=True)
    lender_middle_name = CharField(required=False, allow_null=True)
    lender_prefix = CharField(required=False, allow_null=True)
    lender_suffix = CharField(required=False, allow_null=True)
    lender_street_1 = CharField(required=False, allow_null=True)
    lender_street_2 = CharField(required=False, allow_null=True)
    lender_city = CharField(required=False, allow_null=True)
    lender_state = CharField(required=False, allow_null=True)
    lender_zip = CharField(required=False, allow_null=True)
    lender_committee_id_number = CharField(required=False, allow_null=True)
    lender_candidate_id_number = CharField(required=False, allow_null=True)
    lender_candidate_first_name = CharField(required=False, allow_null=True)
    lender_candidate_last_name = CharField(required=False, allow_null=True)
    lender_candidate_middle_name = CharField(required=False, allow_null=True)
    lender_candidate_prefix = CharField(required=False, allow_null=True)
    lender_candidate_suffix = CharField(required=False, allow_null=True)
    lender_candidate_office = CharField(required=False, allow_null=True)
    lender_candidate_state = CharField(required=False, allow_null=True)
    lender_candidate_district = CharField(required=False, allow_null=True)

    def create(self, validated_data):
        model_data = get_model_data(validated_data, ScheduleC)
        return ScheduleC.objects.create(**model_data)

    class Meta:
        fields = [
            f.name
            for f in ScheduleC._meta.get_fields()
            if f.name not in ["transaction"]
        ] + CONTACT_FIELDS
        model = ScheduleC
