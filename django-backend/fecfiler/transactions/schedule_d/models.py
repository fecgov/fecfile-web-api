from django.db import models
import uuid


class ScheduleD(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    receipt_line_number = models.TextField(null=True, blank=True)
    creditor_organization_name = models.TextField(null=True, blank=True)
    creditor_last_name = models.TextField(null=True, blank=True)
    creditor_first_name = models.TextField(null=True, blank=True)
    creditor_middle_name = models.TextField(null=True, blank=True)
    creditor_prefix = models.TextField(null=True, blank=True)
    creditor_suffix = models.TextField(null=True, blank=True)
    creditor_street_1 = models.TextField(null=True, blank=True)
    creditor_street_2 = models.TextField(null=True, blank=True)
    creditor_city = models.TextField(null=True, blank=True)
    creditor_state = models.TextField(null=True, blank=True)
    creditor_zip = models.TextField(null=True, blank=True)
    purpose_of_debt_or_obligation = models.TextField(null=True, blank=True)
    beginning_balance = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    incurred_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    balance_at_close = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )

    def get_date(self):
        return self.transaction.report.through_date

    def get_transaction(self):
        return self.transaction_set.first()

    def update_with_contact(self, contact):
        transaction = self.get_transaction()
        if contact.id == transaction.contact_1_id:
            self.creditor_organization_name = contact.name
            self.creditor_last_name = contact.last_name
            self.creditor_first_name = contact.first_name
            self.creditor_middle_name = contact.middle_name
            self.creditor_prefix = contact.prefix
            self.creditor_suffix = contact.suffix
            self.creditor_street_1 = contact.street_1
            self.creditor_street_2 = contact.street_2
            self.creditor_city = contact.city
            self.creditor_state = contact.state
            self.creditor_zip = contact.zip
        self.save()

    class Meta:
        app_label = "transactions"
