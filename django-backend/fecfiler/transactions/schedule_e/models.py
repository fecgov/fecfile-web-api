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
    election_code = models.TextField(null=True, blank=True)
    election_other_description = models.TextField(null=True, blank=True)
    dissemination_date = models.DateField(null=True, blank=True)
    expenditure_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    disbursement_date = models.DateField(null=True, blank=True)
    expenditure_purpose_descrip = models.TextField(null=True, blank=True)
    category_code = models.TextField(null=True, blank=True)
    payee_cmtte_fec_id_number = models.TextField(null=True, blank=True)
    support_oppose_code = models.TextField(null=True, blank=True)
    completing_last_name = models.TextField(null=True, blank=True)
    completing_first_name = models.TextField(null=True, blank=True)
    completing_middle_name = models.TextField(null=True, blank=True)
    completing_prefix = models.TextField(null=True, blank=True)
    completing_suffix = models.TextField(null=True, blank=True)
    date_signed = models.DateField(null=True, blank=True)
    memo_text_description = models.TextField(null=True, blank=True)

    def get_transaction(self):
        return self.transaction_set.first()

    class Meta:
        app_label = "transactions"
