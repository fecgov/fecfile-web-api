from rest_framework.serializers import (
    CharField,
    ModelSerializer,
)
from fecfiler.transactions.schedule_b.models import ScheduleB
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
    'payee_employer',
    'payee_occupation',
    'beneficiary_committee_fec_id',
    'beneficiary_candidate_first_name',
    'beneficiary_candidate_last_name',
    'beneficiary_candidate_middle_name',
    'beneficiary_candidate_prefix',
    'beneficiary_candidate_suffix',
    'beneficiary_candidate_fec_id',
    'beneficiary_candidate_office',
    'beneficiary_candidate_state',
    'beneficiary_candidate_district',
    'beneficiary_committee_name',
    'beneficiary_committee_fec_id',
]


class ScheduleBSerializer(ModelSerializer):
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
    payee_employer = CharField(required=False, allow_null=True)
    payee_occupation = CharField(required=False, allow_null=True)
    beneficiary_committee_fec_id = CharField(required=False, allow_null=True)
    beneficiary_candidate_first_name = CharField(required=False, allow_null=True)
    beneficiary_candidate_last_name = CharField(required=False, allow_null=True)
    beneficiary_candidate_middle_name = CharField(required=False, allow_null=True)
    beneficiary_candidate_prefix = CharField(required=False, allow_null=True)
    beneficiary_candidate_suffix = CharField(required=False, allow_null=True)
    beneficiary_candidate_fec_id = CharField(required=False, allow_null=True)
    beneficiary_candidate_office = CharField(required=False, allow_null=True)
    beneficiary_candidate_state = CharField(required=False, allow_null=True)
    beneficiary_candidate_district = CharField(required=False, allow_null=True)
    beneficiary_committee_name = CharField(required=False, allow_null=True)
    beneficiary_committee_fec_id = CharField(required=False, allow_null=True)

    def create(self, validated_data):
        model_data = get_model_data(validated_data, ScheduleB)
        return ScheduleB.objects.create(**model_data)

    class Meta:
        fields = [
            f.name
            for f in ScheduleB._meta.get_fields()
            if f.name not in ["transaction"]
        ] + CONTACT_FIELDS
        model = ScheduleB
