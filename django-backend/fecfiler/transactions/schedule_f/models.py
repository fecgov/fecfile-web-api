from uuid import uuid4
from django.db.models import (
    TextField,
    BooleanField,
    DecimalField,
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

    def get_transaction(self):
        return self.transaction_set.first()

    class Meta:
        app_label = "transactions"
