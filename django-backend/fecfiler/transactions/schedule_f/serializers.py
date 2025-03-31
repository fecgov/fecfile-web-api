from rest_framework.serializers import ModelSerializer
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
    "payee_employer",
    "payee_occupation",
]

# candidate who the CE is on behalf of
CONTACT_2_FIELDS = [
    "payee_candidate_id_number",
    "payee_candidate_last_name",
    "payee_candidate_first_name",
    "payee_candidate_middle_name",
    "payee_candidate_prefix",
    "payee_candidate_suffix",
    "payee_candidate_street_1",
    "payee_candidate_street_2",
    "payee_candidate_city",
    "payee_candidate_state",
    "payee_candidate_zip",
    "payee_candidate_employer",
    "payee_candidate_occupation",
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
