from django.db import models
import uuid


class ScheduleE(models.Model):
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
    election_code = models.TextField(null=True, blank=True)
    election_other_description = models.TextField(null=True, blank=True)
    dissemination_date = models.DateField(null=True, blank=True)
    expenditure_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    disbursement_date = models.DateField(null=True, blank=True)
    calendar_ytd = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    expenditure_purpose_descrip = models.TextField(null=True, blank=True)
    category_code = models.TextField(null=True, blank=True)
    payee_cmtte_fec_id_number = models.TextField(null=True, blank=True)
    support_oppose_code = models.TextField(null=True, blank=True)
    so_candidate_id_number = models.TextField(null=True, blank=True)
    so_candidate_last_name = models.TextField(null=True, blank=True)
    so_candidate_first_name = models.TextField(null=True, blank=True)
    so_candidate_middle_name = models.TextField(null=True, blank=True)
    so_candidate_prefix = models.TextField(null=True, blank=True)
    so_candidate_suffix = models.TextField(null=True, blank=True)
    so_candidate_office = models.TextField(null=True, blank=True)
    so_candidate_district = models.TextField(null=True, blank=True)
    so_candidate_state = models.TextField(null=True, blank=True)
    completing_last_name = models.TextField(null=True, blank=True)
    completing_first_name = models.TextField(null=True, blank=True)
    completing_middle_name = models.TextField(null=True, blank=True)
    completing_prefix = models.TextField(null=True, blank=True)
    completing_suffix = models.TextField(null=True, blank=True)
    date_signed = models.DateField(null=True, blank=True)
    memo_text_description = models.TextField(null=True, blank=True)

    def get_date(self):
        return self.get_transaction().report.coverage_though_date

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
        self.save()

    class Meta:
        app_label = "transactions"
