from rest_framework.serializers import (
    CharField,
    ModelSerializer,
)
from fecfiler.transactions.schedule_d.models import ScheduleD
from fecfiler.shared.utilities import get_model_data


CONTACT_FIELDS = [
    'creditor_organization_name',
    'creditor_last_name',
    'creditor_first_name',
    'creditor_middle_name',
    'creditor_prefix',
    'creditor_suffix',
    'creditor_street_1',
    'creditor_street_2',
    'creditor_city',
    'creditor_state',
    'creditor_zip',
]

def schedule_d_contact_fields(instance, representation):
    if instance.contact_1:
        representation['creditor_organization_name'] = instance.contact_1.name
        representation['creditor_last_name'] = instance.contact_1.last_name
        representation['creditor_first_name'] = instance.contact_1.first_name
        representation['creditor_middle_name'] = instance.contact_1.middle_name
        representation['creditor_prefix'] = instance.contact_1.prefix
        representation['creditor_suffix'] = instance.contact_1.suffix
        representation['creditor_street_1'] = instance.contact_1.street_1
        representation['creditor_street_2'] = instance.contact_1.street_2
        representation['creditor_city'] = instance.contact_1.city
        representation['creditor_state'] = instance.contact_1.state
        representation['creditor_zip'] = instance.contact_1.zip
    return representation


class ScheduleDSerializer(ModelSerializer):
    creditor_organization_name = CharField(required=False, allow_null=True)
    creditor_last_name = CharField(required=False, allow_null=True)
    creditor_first_name = CharField(required=False, allow_null=True)
    creditor_middle_name = CharField(required=False, allow_null=True)
    creditor_prefix = CharField(required=False, allow_null=True)
    creditor_suffix = CharField(required=False, allow_null=True)
    creditor_street_1 = CharField(required=False, allow_null=True)
    creditor_street_2 = CharField(required=False, allow_null=True)
    creditor_city = CharField(required=False, allow_null=True)
    creditor_state = CharField(required=False, allow_null=True)
    creditor_zip = CharField(required=False, allow_null=True)

    def create(self, validated_data):
        model_data = get_model_data(validated_data, ScheduleD)
        return ScheduleD.objects.create(**model_data)

    class Meta:
        fields = [
            f.name
            for f in ScheduleD._meta.get_fields()
            if f.name not in ["transaction"]
        ] + CONTACT_FIELDS
        model = ScheduleD