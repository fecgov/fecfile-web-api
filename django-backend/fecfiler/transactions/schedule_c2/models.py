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
    guaranteed_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )

    def get_transaction(self):
        return self.transaction_set.first()

    class Meta:
        app_label = "transactions"
