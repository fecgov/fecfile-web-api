from rest_framework.serializers import (
    CharField,
    ModelSerializer,
)
from fecfiler.transactions.schedule_c2.models import ScheduleC2
from fecfiler.shared.utilities import get_model_data


CONTACT_FIELDS = [
    'guarantor_last_name',
    'guarantor_first_name',
    'guarantor_middle_name',
    'guarantor_prefix',
    'guarantor_suffix',
    'guarantor_street_1',
    'guarantor_street_2',
    'guarantor_city',
    'guarantor_state',
    'guarantor_zip',
    'guarantor_employer',
    'guarantor_occupation',
]

def schedule_c2_contact_fields(instance, representation):
    if instance.contact_1:
        representation['guarantor_last_name'] = instance.contact_1.last_name
        representation['guarantor_first_name'] = instance.contact_1.first_name
        representation['guarantor_middle_name'] = instance.contact_1.middle_name
        representation['guarantor_prefix'] = instance.contact_1.prefix
        representation['guarantor_suffix'] = instance.contact_1.suffix
        representation['guarantor_street_1'] = instance.contact_1.street_1
        representation['guarantor_street_2'] = instance.contact_1.street_2
        representation['guarantor_city'] = instance.contact_1.city
        representation['guarantor_state'] = instance.contact_1.state
        representation['guarantor_zip'] = instance.contact_1.zip
        representation['guarantor_employer'] = instance.contact_1.employer
        representation['guarantor_occupation'] = instance.contact_1.occupation
    return representation


class ScheduleC2Serializer(ModelSerializer):
    guarantor_last_name = CharField(required=False, allow_null=True)
    guarantor_first_name = CharField(required=False, allow_null=True)
    guarantor_middle_name = CharField(required=False, allow_null=True)
    guarantor_prefix = CharField(required=False, allow_null=True)
    guarantor_suffix = CharField(required=False, allow_null=True)
    guarantor_street_1 = CharField(required=False, allow_null=True)
    guarantor_street_2 = CharField(required=False, allow_null=True)
    guarantor_city = CharField(required=False, allow_null=True)
    guarantor_state = CharField(required=False, allow_null=True)
    guarantor_zip = CharField(required=False, allow_null=True)
    guarantor_employer = CharField(required=False, allow_null=True)
    guarantor_occupation = CharField(required=False, allow_null=True)

    def create(self, validated_data):
        model_data = get_model_data(validated_data, ScheduleC2)
        return ScheduleC2.objects.create(**model_data)

    class Meta:
        fields = [
            f.name
            for f in ScheduleC2._meta.get_fields()
            if f.name not in ["transaction"]
        ] + CONTACT_FIELDS
        model = ScheduleC2