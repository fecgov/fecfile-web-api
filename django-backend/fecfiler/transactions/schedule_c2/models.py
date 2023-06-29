from django.db import models
import uuid


class ScheduleC2(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    guarantor_last_name = models.TextField(null=True, blank=True)
    guarantor_first_name = models.TextField(null=True, blank=True)
    guarantor_middle_name = models.TextField(null=True, blank=True)
    guarantor_prefix = models.TextField(null=True, blank=True)
    guarantor_suffix = models.TextField(null=True, blank=True)
    guarantor_street_1 = models.TextField(null=True, blank=True)
    guarantor_street_2 = models.TextField(null=True, blank=True)
    guarantor_city = models.TextField(null=True, blank=True)
    guarantor_state = models.TextField(null=True, blank=True)
    guarantor_zip = models.TextField(null=True, blank=True)
    guarantor_employer = models.TextField(null=True, blank=True)
    guarantor_occupation = models.TextField(null=True, blank=True)
    guaranteed_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )

    def get_date(self):
        return self.transaction.report.through_date

    def update_with_contact(self, contact):
        self.guarantor_last_name = contact.last_name
        self.guarantor_first_name = contact.first_name
        self.guarantor_middle_name = contact.middle_name
        self.guarantor_prefix = contact.prefix
        self.guarantor_suffix = contact.suffix
        self.guarantor_street_1 = contact.street_1
        self.guarantor_street_2 = contact.street_2
        self.guarantor_city = contact.city
        self.guarantor_state = contact.state
        self.guarantor_zip = contact.zip
        self.guarantor_employer = contact.employer
        self.guarantor_occupation = contact.occupation
        self.save()

    class Meta:
        app_label = "transactions"
