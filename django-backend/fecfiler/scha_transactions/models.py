from django.db import models
from fecfiler.core.models import SoftDeleteModel


class SchATransaction(SoftDeleteModel):
    """Generated model from json schema"""

    form_type = models.TextField(null=False, blank=False, max_length=8, min_length=0)
    filer_committee_id_number = models.TextField(
        null=False, blank=False, max_length=9, min_length=0
    )
    transaction_id = models.TextField(
        null=False, blank=False, max_length=20, min_length=0
    )
    back_reference_tran_id_number = models.TextField(
        null=True, blank=True, max_length=20, min_length=0
    )
    back_reference_sched_name = models.TextField(
        null=True, blank=True, max_length=8, min_length=0
    )
    entity_type = models.TextField(null=False, blank=False, max_length=3, min_length=0)
    contributor_organization_name = models.TextField(
        null=False, blank=False, max_length=200, min_length=0
    )
    contributor_last_name = models.TextField(
        null=False, blank=False, max_length=30, min_length=0
    )
    contributor_first_name = models.TextField(
        null=False, blank=False, max_length=20, min_length=0
    )
    contributor_middle_name = models.TextField(
        null=True, blank=True, max_length=20, min_length=0
    )
    contributor_prefix = models.TextField(
        null=True, blank=True, max_length=10, min_length=0
    )
    contributor_suffix = models.TextField(
        null=True, blank=True, max_length=10, min_length=0
    )
    contributor_street_1 = models.TextField(
        null=True, blank=True, max_length=34, min_length=0
    )
    contributor_street_2 = models.TextField(
        null=True, blank=True, max_length=34, min_length=0
    )
    contributor_city = models.TextField(
        null=True, blank=True, max_length=30, min_length=0
    )
    contributor_state = models.TextField(
        null=True, blank=True, max_length=2, min_length=0
    )
    contributor_zip = models.TextField(
        null=True, blank=True, max_length=9, min_length=0
    )
    election_code = models.TextField(null=True, blank=True, max_length=5, min_length=0)
    election_other_description = models.TextField(
        null=True, blank=True, max_length=20, min_length=0
    )
    contribution_date = models.TextField(
        null=True, blank=True, max_length=8, min_length=8
    )
    contribution_amount = models.IntegerField(null=True, blank=True)
    contribution_aggregate = models.IntegerField(null=True, blank=True)
    contribution_purpose_descrip = models.TextField(
        null=True, blank=True, max_length=100, min_length=0
    )
    contributor_employer = models.TextField(
        null=True, blank=True, max_length=38, min_length=0
    )
    contributor_occupation = models.TextField(
        null=True, blank=True, max_length=38, min_length=0
    )
    donor_committee_fec_id = models.TextField(
        null=True, blank=True, max_length=9, min_length=0
    )
    donor_committee_name = models.TextField(
        null=True, blank=True, max_length=200, min_length=0
    )
    donor_candidate_fec_id = models.TextField(
        null=True, blank=True, max_length=9, min_length=0
    )
    donor_candidate_last_name = models.TextField(
        null=True, blank=True, max_length=30, min_length=0
    )
    donor_candidate_first_name = models.TextField(
        null=True, blank=True, max_length=20, min_length=0
    )
    donor_candidate_middle_name = models.TextField(
        null=True, blank=True, max_length=20, min_length=0
    )
    donor_candidate_prefix = models.TextField(
        null=True, blank=True, max_length=10, min_length=0
    )
    donor_candidate_suffix = models.TextField(
        null=True, blank=True, max_length=10, min_length=0
    )
    donor_candidate_office = models.TextField(
        null=True, blank=True, max_length=1, min_length=0
    )
    donor_candidate_state = models.TextField(
        null=True, blank=True, max_length=2, min_length=0
    )
    donor_candidate_district = models.TextField(
        null=True, blank=True, max_length=2, min_length=2
    )
    conduit_name = models.TextField(null=True, blank=True, max_length=200, min_length=0)
    conduit_street1 = models.TextField(
        null=True, blank=True, max_length=34, min_length=0
    )
    conduit_street2 = models.TextField(
        null=True, blank=True, max_length=34, min_length=0
    )
    conduit_city = models.TextField(null=True, blank=True, max_length=30, min_length=0)
    conduit_state = models.TextField(null=True, blank=True, max_length=2, min_length=0)
    conduit_zip = models.TextField(null=True, blank=True, max_length=9, min_length=0)
    memo_code = models.TextField(null=True, blank=True, max_length=1, min_length=0)
    memo_text_description = models.TextField(
        null=True, blank=True, max_length=100, min_length=0
    )
    reference_to_si_or_sl_system_code_that_identifies_the_account = models.TextField(
        null=True, blank=True, max_length=9, min_length=0
    )
    transaction_type_identifier = models.TextField(
        null=True, blank=True, max_length=12, min_length=0
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scha_transactions"
