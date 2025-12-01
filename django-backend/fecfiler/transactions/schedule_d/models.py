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
    purpose_of_debt_or_obligation = models.TextField(null=True, blank=True)
    incurred_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    incurred_prior = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    payment_prior = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    payment_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    beginning_balance = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    balance_at_close = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    # saved on schedule record to avoid joining on report
    report_coverage_from_date = models.DateField(null=True, blank=True)

    def get_transaction(self):
        return self.transaction_set.first()

    def get_date(self):
        return None

    class Meta:
        app_label = "transactions"
