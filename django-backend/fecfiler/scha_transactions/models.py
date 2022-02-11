from django.db import models
import logging

logger = logging.getLogger(__name__)


class SchATransaction(models.Model):
    """Generated model from json schema"""

    form_type = models.CharField(null=False, blank=False, max_length=8)
    filer_committee_id_number = models.CharField(null=False, blank=False, max_length=9)
    transaction_id = models.CharField(null=False, blank=False, max_length=20)
    back_reference_tran_id_number = models.CharField(
        null=True, blank=True, max_length=20
    )
    back_reference_sched_name = models.CharField(null=True, blank=True, max_length=8)
    entity_type = models.CharField(null=False, blank=False, max_length=3)
    contributor_organization_name = models.CharField(
        null=False, blank=False, max_length=200
    )
    contributor_last_name = models.CharField(null=False, blank=False, max_length=30)
    contributor_first_name = models.CharField(null=False, blank=False, max_length=20)
    contributor_middle_name = models.CharField(null=True, blank=True, max_length=20)
    contributor_prefix = models.CharField(null=True, blank=True, max_length=10)
    contributor_suffix = models.CharField(null=True, blank=True, max_length=10)
    contributor_street_1 = models.CharField(null=True, blank=True, max_length=34)
    contributor_street_2 = models.CharField(null=True, blank=True, max_length=34)
    contributor_city = models.CharField(null=True, blank=True, max_length=30)
    contributor_state = models.CharField(null=True, blank=True, max_length=2)
    contributor_zip = models.CharField(null=True, blank=True, max_length=9)
    election_code = models.CharField(null=True, blank=True, max_length=5)
    election_other_description = models.CharField(null=True, blank=True, max_length=20)
    contribution_date = models.IntegerField(null=True, blank=True)
    contribution_amount = models.IntegerField(null=True, blank=True)
    contribution_aggregate = models.IntegerField(null=True, blank=True)
    contribution_purpose_descrip = models.CharField(
        null=True, blank=True, max_length=100
    )
    contributor_employer = models.CharField(null=True, blank=True, max_length=38)
    contributor_occupation = models.CharField(null=True, blank=True, max_length=38)
    donor_committee_fec_id = models.CharField(null=True, blank=True, max_length=9)
    donor_committee_name = models.CharField(null=True, blank=True, max_length=200)
    donor_candidate_fec_id = models.CharField(null=True, blank=True, max_length=9)
    donor_candidate_last_name = models.CharField(null=True, blank=True, max_length=30)
    donor_candidate_first_name = models.CharField(null=True, blank=True, max_length=20)
    donor_candidate_middle_name = models.CharField(null=True, blank=True, max_length=20)
    donor_candidate_prefix = models.CharField(null=True, blank=True, max_length=10)
    donor_candidate_suffix = models.CharField(null=True, blank=True, max_length=10)
    donor_candidate_office = models.CharField(null=True, blank=True, max_length=1)
    donor_candidate_state = models.CharField(null=True, blank=True, max_length=2)
    donor_candidate_district = models.IntegerField(null=True, blank=True)
    conduit_name = models.CharField(null=True, blank=True, max_length=200)
    conduit_street1 = models.CharField(null=True, blank=True, max_length=34)
    conduit_street2 = models.CharField(null=True, blank=True, max_length=34)
    conduit_city = models.CharField(null=True, blank=True, max_length=30)
    conduit_state = models.CharField(null=True, blank=True, max_length=2)
    conduit_zip = models.CharField(null=True, blank=True, max_length=9)
    memo_code = models.CharField(null=True, blank=True, max_length=1)
    memo_text_description = models.CharField(null=True, blank=True, max_length=100)
    reference_to_si_or_sl_system_code_that_identifies_the_account = models.CharField(
        null=True, blank=True, max_length=9
    )
    transaction_type_identifier = models.CharField(null=True, blank=True, max_length=12)
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)

    class Meta:
        db_table = "scha_transactions"
