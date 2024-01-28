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

def add_schedule_b_contact_fields(instance, representation):
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
        representation['payee_employer'] = instance.contact_1.employer
        representation['payee_occupation'] = instance.contact_1.occupation
        representation['beneficiary_committee_name'] = instance.contact_1.name
        representation['beneficiary_committee_fec_id'] = instance.contact_1.committee_id
    if instance.contact_2:
        representation['beneficiary_candidate_first_name'] = instance.contact_2.first_name
        representation['beneficiary_candidate_last_name'] = instance.contact_2.last_name
        representation['beneficiary_candidate_middle_name'] = instance.contact_2.middle_name
        representation['beneficiary_candidate_prefix'] = instance.contact_2.prefix
        representation['beneficiary_candidate_suffix'] = instance.contact_2.suffix
        representation['beneficiary_candidate_fec_id'] = instance.contact_2.candidate_id
        representation['beneficiary_candidate_office'] = instance.contact_2.candidate_office
        representation['beneficiary_candidate_state'] = instance.contact_2.candidate_state
        representation['beneficiary_candidate_district'] = instance.contact_2.candidate_district
    if instance.contact_3:
        # If it exists, contact_3 committee info overrides the info from contact_1
        # See IN_KIND_CONTRIBUTIONS transaction types
        representation['beneficiary_committee_name'] = instance.contact_3.name
        representation['beneficiary_committee_fec_id'] = instance.contact_3.committee_id


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