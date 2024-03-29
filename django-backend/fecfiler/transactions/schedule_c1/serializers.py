from rest_framework.serializers import (
    CharField,
    ModelSerializer,
)
from fecfiler.transactions.schedule_c1.models import ScheduleC1
from fecfiler.shared.utilities import get_model_data


CONTACT_FIELDS = [
    'lender_organization_name',
    'lender_street_1',
    'lender_street_2',
    'lender_city',
    'lender_state',
    'lender_zip',
]


class ScheduleC1Serializer(ModelSerializer):
    lender_organization_name = CharField(required=False, allow_null=True)
    lender_street_1 = CharField(required=False, allow_null=True)
    lender_street_2 = CharField(required=False, allow_null=True)
    lender_city = CharField(required=False, allow_null=True)
    lender_state = CharField(required=False, allow_null=True)
    lender_zip = CharField(required=False, allow_null=True)

    def create(self, validated_data):
        model_data = get_model_data(validated_data, ScheduleC1)
        return ScheduleC1.objects.create(**model_data)

    class Meta:
        fields = [
            f.name
            for f in ScheduleC1._meta.get_fields()
            if f.name not in ["transaction"]
        ] + CONTACT_FIELDS
        model = ScheduleC1
