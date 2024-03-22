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
    election_code = models.TextField(null=True, blank=True)
    election_other_description = models.TextField(null=True, blank=True)
    loan_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    loan_incurred_date = models.DateField(null=True, blank=True)
    loan_due_date = models.TextField(null=True, blank=True)
    loan_interest_rate = models.TextField(null=True, blank=True)
    secured = models.BooleanField(null=True, blank=True, default=False)
    personal_funds = models.BooleanField(null=True, blank=True, default=False)
    memo_text_description = models.TextField(null=True, blank=True)

    def get_transaction(self):
        return self.transaction_set.first()

    class Meta:
        app_label = "transactions"
