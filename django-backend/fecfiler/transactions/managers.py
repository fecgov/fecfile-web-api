from fecfiler.soft_delete.managers import SoftDeleteManager
from fecfiler.transactions.schedule_a.managers import (
    over_two_hundred_types as schedule_a_over_two_hundred_types,
)
from fecfiler.transactions.schedule_b.managers import (
    over_two_hundred_types as schedule_b_over_two_hundred_types,
)
from django.db.models.functions import Coalesce
from django.db.models import OuterRef, Subquery, Sum, Q, Case, When, Value, BooleanField
from decimal import Decimal

"""Manager to deterimine fields that are used the same way across transactions,
but are called different names"""


class TransactionManager(SoftDeleteManager):
    def get_queryset(self):

        queryset = (
            super()
            .get_queryset()
            .annotate(
                date=Coalesce(
                    "schedule_a__contribution_date",
                    "schedule_b__expenditure_date",
                ),
                amount=Coalesce(
                    "schedule_a__contribution_amount",
                    "schedule_b__expenditure_amount",
                ),
            )
        )

        contact_clause = Q(contact_id=OuterRef("contact_id"))
        year_clause = Q(date__year=OuterRef("date__year"))
        date_clause = Q(date__lt=OuterRef("date")) | Q(
            date=OuterRef("date"),
            created__lte=OuterRef("created"),
        )
        group_clause = Q(aggregation_group=OuterRef("aggregation_group"))

        aggregate_clause = (
            queryset.filter(contact_clause, year_clause, date_clause, group_clause)
            .values("committee_account_id")
            .annotate(aggregate=Sum("amount"))
            .values("aggregate")
        )
        return queryset.annotate(
            aggregate=Subquery(aggregate_clause),
            itemized=self.get_itemization_clause(),
        )

    def get_itemization_clause(self):
        over_two_hundred_types = (
            schedule_a_over_two_hundred_types + schedule_b_over_two_hundred_types
        )
        return Case(
            When(aggregate__lt=Value(Decimal(0)), then=Value(True)),
            When(
                transaction_type_identifier__in=over_two_hundred_types,
                then=Q(aggregate__gt=Value(Decimal(200))),
            ),
            default=Value(True),
            output_field=BooleanField(),
        )
