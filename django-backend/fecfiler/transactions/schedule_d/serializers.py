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

DEFAULT_ZERO_FIELDS = ["beginning_balance", "payment_amount", "payment_prior"]


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

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        for field in DEFAULT_ZERO_FIELDS:
            if representation.get(field) is None:
                representation[field] = "0.00"
        return representation

    class Meta:
        fields = [
            f.name
            for f in ScheduleD._meta.get_fields()
            if f.name not in ["transaction"]
        ] + CONTACT_FIELDS
        model = ScheduleD
