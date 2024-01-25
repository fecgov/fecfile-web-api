from rest_framework.serializers import (
    CharField,
    ModelSerializer,
)
from fecfiler.transactions.schedule_a.models import ScheduleA
from fecfiler.shared.utilities import get_model_data


CONTACT_FIELDS = [
    'contributor_organization_name',
    'contributor_last_name',
    'contributor_first_name',
    'contributor_middle_name',
    'contributor_prefix',
    'contributor_suffix',
    'contributor_street_1',
    'contributor_street_2',
    'contributor_city',
    'contributor_state',
    'contributor_zip',
    'contributor_employer',
    'contributor_occupation',
    'donor_committee_fec_id',
    'donor_candidate_last_name',
    'donor_candidate_first_name',
    'donor_candidate_middle_name',
    'donor_candidate_prefix',
    'donor_candidate_suffix',
    'donor_candidate_office',
    'donor_candidate_state',
    'donor_candidate_district',
    'donor_committee_name',
    'donor_committee_fec_id', 
]

def schedule_a_contact_fields(instance, representation):
    if instance.contact_1:
        representation['contributor_organization_name'] = instance.contact_1.name
        representation['contributor_last_name'] = instance.contact_1.last_name
        representation['contributor_first_name'] = instance.contact_1.first_name
        representation['contributor_middle_name'] = instance.contact_1.middle_name
        representation['contributor_prefix'] = instance.contact_1.prefix
        representation['contributor_suffix'] = instance.contact_1.suffix
        representation['contributor_street_1'] = instance.contact_1.street_1
        representation['contributor_street_2'] = instance.contact_1.street_2
        representation['contributor_city'] = instance.contact_1.city
        representation['contributor_state'] = instance.contact_1.state
        representation['contributor_zip'] = instance.contact_1.zip
        representation['contributor_employer'] = instance.contact_1.employer
        representation['contributor_occupation'] = instance.contact_1.occupation
        representation['donor_committee_fec_id'] = instance.contact_1.committee_id
    if instance.contact_2:
        representation['donor_candidate_fec_id'] = instance.contact_2.candidate_id
        representation['donor_candidate_last_name'] = instance.contact_2.last_name
        representation['donor_candidate_first_name'] = instance.contact_2.first_name
        representation['donor_candidate_middle_name'] = instance.contact_2.middle_name
        representation['donor_candidate_prefix'] = instance.contact_2.prefix
        representation['donor_candidate_suffix'] = instance.contact_2.suffix
        representation['donor_candidate_office'] = instance.contact_2.candidate_office
        representation['donor_candidate_state'] = instance.contact_2.candidate_state
        representation['donor_candidate_district'] = instance.contact_2.candidate_district
    if instance.contact_3:
        representation['donor_committee_name'] = instance.contact_3.name
        representation['donor_committee_fec_id'] = instance.contact_3.committee_id
    return representation


class ScheduleASerializer(ModelSerializer):
    contributor_organization_name = CharField(required=False, allow_null=True)
    contributor_last_name = CharField(required=False, allow_null=True)
    contributor_first_name = CharField(required=False, allow_null=True)
    contributor_middle_name = CharField(required=False, allow_null=True)
    contributor_prefix = CharField(required=False, allow_null=True)
    contributor_suffix = CharField(required=False, allow_null=True)
    contributor_street_1 = CharField(required=False, allow_null=True)
    contributor_street_2 = CharField(required=False, allow_null=True)
    contributor_city = CharField(required=False, allow_null=True)
    contributor_state = CharField(required=False, allow_null=True)
    contributor_zip = CharField(required=False, allow_null=True)
    contributor_employer = CharField(required=False, allow_null=True)
    contributor_occupation = CharField(required=False, allow_null=True)
    donor_committee_fec_id = CharField(required=False, allow_null=True)
    donor_candidate_last_name = CharField(required=False, allow_null=True)
    donor_candidate_first_name = CharField(required=False, allow_null=True)
    donor_candidate_middle_name = CharField(required=False, allow_null=True)
    donor_candidate_prefix = CharField(required=False, allow_null=True)
    donor_candidate_suffix = CharField(required=False, allow_null=True)
    donor_candidate_office = CharField(required=False, allow_null=True)
    donor_candidate_state = CharField(required=False, allow_null=True)
    donor_candidate_district = CharField(required=False, allow_null=True)
    donor_committee_name = CharField(required=False, allow_null=True)
    donor_committee_fec_id = CharField(required=False, allow_null=True)

    def create(self, validated_data):
        model_data = get_model_data(validated_data, ScheduleA)
        return ScheduleA.objects.create(**model_data)

    class Meta:
        fields = [
            f.name
            for f in ScheduleA._meta.get_fields()
            if f.name not in ["transaction"]
        ] + CONTACT_FIELDS
        model = ScheduleA