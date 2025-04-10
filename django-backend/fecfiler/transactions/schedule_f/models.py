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
    filer_designated_to_make_coordinated_expenditures = BooleanField(
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

    category_code = TextField(null=True, blank=True)

    general_election_year = TextField(blank=True)

    memo_text_description = TextField(null=True, blank=True)

    def get_transaction(self):
        return self.transaction_set.first()

    def get_date(self):
        return self.expenditure_date

    class Meta:
        app_label = "transactions"
