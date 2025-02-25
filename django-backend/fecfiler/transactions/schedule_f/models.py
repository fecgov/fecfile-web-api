from django.db import models
import uuid


class ScheduleF(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    has_filer_been_designated = models.BooleanField(null=True, blank=True)
    designating_committee_account = models.ForeignKey(
        "committee_accounts.CommitteeAccount", on_delete=models.CASCADE, null=True
    )
    designating_committee_name = models.TextField(blank=True)

    expenditure_date = models.DateField(null=True, blank=True)
    expenditure_amount = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    aggregate_general_elec_expended = models.DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    expenditure_purpose_descrip = models.TextField(blank=True)

    category_code = models.TextField(blank=True)

    memo_text_description = models.TextField(blank=True)

    @property
    def designating_committee_id_number(self):
        if not self.designating_committee_account:
            return None

        return self.designating_committee_account.committee_id

    def get_transaction(self):
        return self.transaction_set.first()

    class Meta:
        app_label = "transactions"
