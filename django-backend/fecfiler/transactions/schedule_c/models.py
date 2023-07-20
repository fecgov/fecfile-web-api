from django.db import models
import uuid


class ScheduleC(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    receipt_line_number = models.TextField(null=True, blank=True)
    lender_organization_name = models.TextField(null=True, blank=True)
    lender_last_name = models.TextField(null=True, blank=True)
    lender_first_name = models.TextField(null=True, blank=True)
    lender_middle_name = models.TextField(null=True, blank=True)
    lender_prefix = models.TextField(null=True, blank=True)
    lender_suffix = models.TextField(null=True, blank=True)
    lender_street_1 = models.TextField(null=True, blank=True)
    lender_street_2 = models.TextField(null=True, blank=True)
    lender_city = models.TextField(null=True, blank=True)
    lender_state = models.TextField(null=True, blank=True)
    lender_zip = models.TextField(null=True, blank=True)
    election_code = models.TextField(null=True, blank=True)
    election_other_description = models.TextField(null=True, blank=True)
    loan_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    loan_payment_to_date = models.TextField(null=True, blank=True)
    loan_balance = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    loan_incurred_date = models.DateField(null=True, blank=True)
    loan_due_date = models.DateField(null=True, blank=True)
    loan_interest_rate = models.DecimalField(
        null=True, blank=True, max_digits=14, decimal_places=14
    )
    secured = models.BooleanField(null=True, blank=True, default=False)
    personal_funds = models.BooleanField(null=True, blank=True, default=False)
    lender_committee_id_number = models.TextField(null=True, blank=True)
    lender_candidate_id_number = models.TextField(null=True, blank=True)
    lender_candidate_last_name = models.TextField(null=True, blank=True)
    lender_candidate_first_name = models.TextField(null=True, blank=True)
    lender_candidate_middle_name = models.TextField(null=True, blank=True)
    lender_candidate_prefix = models.TextField(null=True, blank=True)
    lender_candidate_suffix = models.TextField(null=True, blank=True)
    lender_candidate_office = models.TextField(null=True, blank=True)
    lender_candidate_state = models.TextField(null=True, blank=True)
    lender_candidate_district = models.TextField(null=True, blank=True)
    memo_text_description = models.TextField(null=True, blank=True)

    def get_date(self):
        return self.transaction.report.through_date

    def get_transaction(self):
        return self.transaction_set.first()

    def update_with_contact(self, contact):
        transaction = self.get_transaction()
        if contact.id == transaction.contact_1_id:
            self.lender_organization_name = contact.name
            self.lender_last_name = contact.last_name
            self.lender_first_name = contact.first_name
            self.lender_middle_name = contact.middle_name
            self.lender_prefix = contact.prefix
            self.lender_suffix = contact.suffix
            self.lender_street_1 = contact.street_1
            self.lender_street_2 = contact.street_2
            self.lender_city = contact.city
            self.lender_state = contact.state
            self.lender_zip = contact.zip
            self.lender_employer = contact.employer
            self.lender_occupation = contact.occupation
            self.lender_committee_id_number = contact.committee_id
        if contact.id == transaction.contact_2_id:
            self.lender_candidate_first_name = contact.first_name
            self.lender_candidate_last_name = contact.last_name
            self.lender_candidate_middle_name = contact.middle_name
            self.lender_candidate_prefix = contact.prefix
            self.lender_candidate_suffix = contact.suffix
            self.lender_candidate_id_number = contact.candidate_id
            self.lender_candidate_office = contact.candidate_office
            self.lender_candidate_state = contact.candidate_state
            self.lender_candidate_district = contact.candidate_district
        # Schedule C transactions do not require Contact 3
        self.save()

    class Meta:
        app_label = "transactions"
