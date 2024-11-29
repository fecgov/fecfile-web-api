from django.db import models, transaction as db_transaction
from fecfiler.reports.models import Report
from fecfiler.committee_accounts.models import CommitteeOwnedModel
import uuid


class CashOnHandYearly(CommitteeOwnedModel):

    id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )

    year = models.TextField(null=False, blank=False)
    cash_on_hand = models.DecimalField(
        null=False, blank=False, max_digits=11, decimal_places=2
    )
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        with db_transaction.atomic():
            super(CashOnHandYearly, self).save(*args, **kwargs)
            Report.objects.filter(
                committee_account=self.committee_account,
            ).update(calculation_status=None)

    class Meta:
        db_table = "cash_on_hand_yearly"
