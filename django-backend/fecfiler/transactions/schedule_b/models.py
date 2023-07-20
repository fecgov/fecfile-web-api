from django.db import models
import uuid


class ScheduleB(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    payee_organization_name = models.TextField(null=True, blank=True)
    payee_last_name = models.TextField(null=True, blank=True)
    payee_first_name = models.TextField(null=True, blank=True)
    payee_middle_name = models.TextField(null=True, blank=True)
    payee_prefix = models.TextField(null=True, blank=True)
    payee_suffix = models.TextField(null=True, blank=True)
    payee_street_1 = models.TextField(null=True, blank=True)
    payee_street_2 = models.TextField(null=True, blank=True)
    payee_city = models.TextField(null=True, blank=True)
    payee_state = models.TextField(null=True, blank=True)
    payee_zip = models.TextField(null=True, blank=True)

    expenditure_date = models.DateField(null=True, blank=True)
    expenditure_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )

    expenditure_purpose_descrip = models.TextField(null=True, blank=True)

    election_code = models.TextField(null=True, blank=True)
    election_other_description = models.TextField(null=True, blank=True)
    conduit_name = models.TextField(null=True, blank=True)
    conduit_street_1 = models.TextField(null=True, blank=True)
    conduit_street_2 = models.TextField(null=True, blank=True)
    conduit_city = models.TextField(null=True, blank=True)
    conduit_state = models.TextField(null=True, blank=True)
    conduit_zip = models.TextField(null=True, blank=True)

    category_code = models.TextField(null=True, blank=True)

    beneficiary_committee_fec_id = models.TextField(null=True, blank=True)
    beneficiary_committee_name = models.TextField(null=True, blank=True)
    beneficiary_candidate_fec_id = models.TextField(null=True, blank=True)
    beneficiary_candidate_last_name = models.TextField(null=True, blank=True)
    beneficiary_candidate_first_name = models.TextField(null=True, blank=True)
    beneficiary_candidate_middle_name = models.TextField(null=True, blank=True)
    beneficiary_candidate_prefix = models.TextField(null=True, blank=True)
    beneficiary_candidate_suffix = models.TextField(null=True, blank=True)
    beneficiary_candidate_office = models.TextField(null=True, blank=True)
    beneficiary_candidate_state = models.TextField(null=True, blank=True)
    beneficiary_candidate_district = models.TextField(null=True, blank=True)

    memo_text_description = models.TextField(null=True, blank=True)
    reference_to_si_or_sl_system_code_that_identifies_the_account = models.TextField(
        null=True, blank=True
    )

    def get_date(self):
        return self.expenditure_date

    def get_transaction(self):
        return self.transaction_set.first()

    def update_with_contact(self, contact):
        transaction = self.get_transaction()
        if contact.id == transaction.contact_1_id:
            self.payee_organization_name = contact.name
            self.payee_last_name = contact.last_name
            self.payee_first_name = contact.first_name
            self.payee_middle_name = contact.middle_name
            self.payee_prefix = contact.prefix
            self.payee_suffix = contact.suffix
            self.payee_street_1 = contact.street_1
            self.payee_street_2 = contact.street_2
            self.payee_city = contact.city
            self.payee_state = contact.state
            self.payee_zip = contact.zip
            self.payee_employer = contact.employer
            self.payee_occupation = contact.occupation
            self.beneficiary_committee_fec_id = contact.committee_id
        if contact.id == transaction.contact_2_id:
            self.beneficiary_candidate_first_name = contact.first_name
            self.beneficiary_candidate_last_name = contact.last_name
            self.beneficiary_candidate_middle_name = contact.middle_name
            self.beneficiary_candidate_prefix = contact.prefix
            self.beneficiary_candidate_suffix = contact.suffix
            self.beneficiary_candidate_fec_id = contact.candidate_id
            self.beneficiary_candidate_office = contact.candidate_office
            self.beneficiary_candidate_state = contact.candidate_state
            self.beneficiary_candidate_district = contact.candidate_district
        if contact.id == transaction.contact_3_id:
            self.beneficiary_committee_name = contact.name
            self.beneficiary_committee_fec_id = contact.committee_id
        self.save()

    class Meta:
        app_label = "transactions"
