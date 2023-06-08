from django.db import models
import uuid


class ScheduleA(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
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

    contribution_date = models.DateField(null=True, blank=True)
    contribution_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )

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

    election_code = models.TextField(null=True, blank=True)
    election_other_description = models.TextField(null=True, blank=True)
    conduit_name = models.TextField(null=True, blank=True)
    conduit_street_1 = models.TextField(null=True, blank=True)
    conduit_street_2 = models.TextField(null=True, blank=True)
    conduit_city = models.TextField(null=True, blank=True)
    conduit_state = models.TextField(null=True, blank=True)
    conduit_zip = models.TextField(null=True, blank=True)

    memo_text_description = models.TextField(null=True, blank=True)
    reference_to_si_or_sl_system_code_that_identifies_the_account = models.TextField(
        null=True, blank=True
    )

    class Meta:
        app_label = "transactions"

    def get_date(self):
        return self.contribution_date

    def get_transaction(self):
        return self.transactions_set.first()

    def update_with_contact(self, contact):
        transaction = self.get_transaction()
        if contact.id == transaction.contact_1_id:
            self.contributor_organization_name = contact.name
            self.contributor_last_name = contact.last_name
            self.contributor_first_name = contact.first_name
            self.contributor_middle_name = contact.middle_name
            self.contributor_prefix = contact.prefix
            self.contributor_suffix = contact.suffix
            self.contributor_street_1 = contact.street_1
            self.contributor_street_2 = contact.street_2
            self.contributor_city = contact.city
            self.contributor_state = contact.state
            self.contributor_zip = contact.zip
            self.contributor_employer = contact.employer
            self.contributor_occupation = contact.occupation
            self.donor_committee_fec_id = contact.committee_id
        if contact.id == transaction.contact_2_id:
            self.donor_candidate_fec_id = contact.fec
            self.donor_candidate_last_name = contact.last_name
            self.donor_candidate_first_name = contact.first_name
            self.donor_candidate_middle_name = contact.middle_name
            self.donor_candidate_prefix = contact.prefix
            self.donor_candidate_suffix = contact.suffix
            self.donor_candidate_office = contact.candidate_office
            self.donor_candidate_state = contact.candidate_state
            self.donor_candidate_district = contact.candidate_district
        self.save()


class ScheduleATransaction(models.Model):
    """stub class until we can figure out how to make migrations run without old models"""

    class Meta:
        app_label = "transactions"
