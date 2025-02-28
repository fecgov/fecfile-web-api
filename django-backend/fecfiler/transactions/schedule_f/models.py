from uuid import uuid4
from django.db.models import (
    TextField,
    ForeignKey,
    BooleanField,
    DecimalField,
    CASCADE,
    DateField,
    UUIDField,
    Model,
)


class ScheduleF(Model):
    id = UUIDField(
        default=uuid4,
        editable=False,
        primary_key=True,
        serialize=False,
        unique=True,
    )
    filer_designated_to_make_coordianted_expenditures = BooleanField(
        null=True, blank=True
    )
    designating_committee_account = ForeignKey(
        "committee_accounts.CommitteeAccount", on_delete=CASCADE, null=True
    )
    designating_committee_name = TextField(blank=True)

    expenditure_date = DateField(null=True, blank=True)
    expenditure_amount = DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    aggregate_general_elec_expended = DecimalField(
        null=True, blank=True, max_digits=11, decimal_places=2
    )
    expenditure_purpose_descrip = TextField(blank=True)

    category_code = TextField(blank=True)

    memo_text_description = TextField(blank=True)

    @property
    def designating_committee_id_number(self):
        if not self.designating_committee_account:
            return None

        return self.designating_committee_account.committee_id

    def get_transaction(self):
        return self.transaction_set.first()

    class Meta:
        app_label = "transactions"
