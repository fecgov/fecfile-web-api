from django.db import models
from fecfiler.soft_delete.models import SoftDeleteModel
from fecfiler.committee_accounts.models import CommitteeOwnedModel


class SchATransaction(SoftDeleteModel, CommitteeOwnedModel):
    """Generated model from json schema"""

    form_type = models.TextField(null=True, blank=True)
    filer_committee_id_number = models.TextField(null=True, blank=True)
    transaction_id = models.TextField(null=True, blank=True)
    back_reference_tran_id_number = models.TextField(null=True, blank=True)
    back_reference_sched_name = models.TextField(null=True, blank=True)
    entity_type = models.TextField(null=True, blank=True)
    contributor_organization_name = models.TextField(null=True, blank=True)
    contributor_last_name = models.TextField(null=True, blank=True)
    contributor_first_name = models.TextField(null=True, blank=True)
    contributor_middle_name = models.TextField(null=True, blank=True)
    contributor_prefix = models.TextField(null=True, blank=True)
    contributor_suffix = models.TextField(null=True, blank=True)
    contributor_street_1 = models.TextField(null=True, blank=True)
    contributor_street_2 = models.TextField(null=True, blank=True)
    contributor_city = models.TextField(null=True, blank=True)
    contributor_state = models.TextField(null=True, blank=True)
    contributor_zip = models.TextField(null=True, blank=True)
    election_code = models.TextField(null=True, blank=True)
    election_other_description = models.TextField(null=True, blank=True)
    contribution_date = models.TextField(null=True, blank=True)
    contribution_amount = models.IntegerField(null=True, blank=True)
    contribution_aggregate = models.IntegerField(null=True, blank=True)
    contribution_purpose_descrip = models.TextField(null=True, blank=True)
    contributor_employer = models.TextField(null=True, blank=True)
    contributor_occupation = models.TextField(null=True, blank=True)
    donor_committee_fec_id = models.TextField(null=True, blank=True)
    donor_committee_name = models.TextField(null=True, blank=True)
    donor_candidate_fec_id = models.TextField(null=True, blank=True)
    donor_candidate_last_name = models.TextField(null=True, blank=True)
    donor_candidate_first_name = models.TextField(null=True, blank=True)
    donor_candidate_middle_name = models.TextField(null=True, blank=True)
    donor_candidate_prefix = models.TextField(null=True, blank=True)
    donor_candidate_suffix = models.TextField(null=True, blank=True)
    donor_candidate_office = models.TextField(null=True, blank=True)
    donor_candidate_state = models.TextField(null=True, blank=True)
    donor_candidate_district = models.TextField(null=True, blank=True)
    conduit_name = models.TextField(null=True, blank=True)
    conduit_street1 = models.TextField(null=True, blank=True)
    conduit_street2 = models.TextField(null=True, blank=True)
    conduit_city = models.TextField(null=True, blank=True)
    conduit_state = models.TextField(null=True, blank=True)
    conduit_zip = models.TextField(null=True, blank=True)
    memo_code = models.BooleanField(null=True, blank=True, default=False)
    memo_text_description = models.TextField(null=True, blank=True)
    reference_to_si_or_sl_system_code_that_identifies_the_account = models.TextField(
        null=True, blank=True
    )
    transaction_type_identifier = models.TextField(null=True, blank=True)
    parent_transaction = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        default=None,
        on_delete=models.CASCADE
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "scha_transactions"
