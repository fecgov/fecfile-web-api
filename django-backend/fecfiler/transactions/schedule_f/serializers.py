from rest_framework.serializers import ModelSerializer, CharField
from fecfiler.transactions.schedule_f.models import ScheduleF
from fecfiler.shared.utilities import get_model_data


# Payee organization or individual
CONTACT_1_FIELDS = [
    "payee_organization_name",
    "payee_last_name",
    "payee_first_name",
    "payee_middle_name",
    "payee_prefix",
    "payee_suffix",
    "payee_street_1",
    "payee_street_2",
    "payee_city",
    "payee_state",
    "payee_zip",
]

# candidate who the CE is on behalf of
CONTACT_2_FIELDS = [
    "payee_candidate_id_number",
    "payee_candidate_last_name",
    "payee_candidate_first_name",
    "payee_candidate_middle_name",
    "payee_candidate_prefix",
    "payee_candidate_suffix",
    "payee_candidate_office",
    "payee_candidate_state",
    "payee_candidate_district",
]

# candidate committee that the CE is on behalf of
CONTACT_3_FIELDS = [
    "payee_committee_id_number",
]

# designating committee
CONTACT_4_FIELDS = [
    "designating_committee_id_number",
    "designating_committee_name",
]

# subordinate committee
CONTACT_5_FIELDS = [
    "subordinate_committee_id_number",
    "subordinate_committee_name",
    "subordinate_street_1",
    "subordinate_street_2",
    "subordinate_city",
    "subordinate_state",
    "subordinate_zip",
]


class ScheduleFSerializer(ModelSerializer):
    # Contact 1
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
    # Contact 2
    payee_candidate_id_number = CharField(required=False, allow_null=True)
    payee_candidate_last_name = CharField(required=False, allow_null=True)
    payee_candidate_first_name = CharField(required=False, allow_null=True)
    payee_candidate_middle_name = CharField(required=False, allow_null=True)
    payee_candidate_prefix = CharField(required=False, allow_null=True)
    payee_candidate_suffix = CharField(required=False, allow_null=True)
    payee_candidate_office = CharField(required=False, allow_null=True)
    payee_candidate_state = CharField(required=False, allow_null=True)
    payee_candidate_district = CharField(required=False, allow_null=True)
    # Contact 3
    payee_committee_id_number = CharField(required=False, allow_null=True)
    # Contact 4
    designating_committee_id_number = CharField(required=False, allow_null=True)
    designating_committee_name = CharField(required=False, allow_null=True)
    # Contact 5
    subordinate_committee_id_number = CharField(required=False, allow_null=True)
    subordinate_committee_name = CharField(required=False, allow_null=True)
    subordinate_street_1 = CharField(required=False, allow_null=True)
    subordinate_street_2 = CharField(required=False, allow_null=True)
    subordinate_city = CharField(required=False, allow_null=True)
    subordinate_state = CharField(required=False, allow_null=True)
    subordinate_zip = CharField(required=False, allow_null=True)

    def create(self, validated_data):
        model_data = get_model_data(validated_data, ScheduleF)
        return ScheduleF.objects.create(**model_data)

    class Meta:
        fields = (
            [
                f.name
                for f in ScheduleF._meta.get_fields()
                if f.name not in ["transaction"]
            ]
            + CONTACT_1_FIELDS
            + CONTACT_2_FIELDS
            + CONTACT_3_FIELDS
            + CONTACT_4_FIELDS
            + CONTACT_5_FIELDS
        )
        model = ScheduleF
