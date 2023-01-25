from fecfiler.soft_delete.managers import SoftDeleteManager
from fecfiler.transactions.schedule_a.managers import (
    over_two_hundred_types as schedule_a_over_two_hundred_types,
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
                action_date=Coalesce(
                    "schedule_a__contribution_date",
                    None,  # , "schedule_b__expenditure_date"
                ),
                action_amount=Coalesce(
                    "schedule_a__contribution_amount",
                    None,  # , "schedule_b__expenditure_amount"
                ),
            )
        )

        contact_clause = Q(contact_id=OuterRef("contact_id"))
        year_clause = Q(action_date__year=OuterRef("action_date__year"))
        date_clause = Q(action_date__lt=OuterRef("action_date")) | Q(
            action_date=OuterRef("action_date"),
            created__lte=OuterRef("created"),
        )
        group_clause = Q(aggregation_group=OuterRef("aggregation_group"))

        aggregate_clause = (
            queryset.filter(contact_clause, year_clause, date_clause, group_clause)
            .values("committee_account_id")
            .annotate(aggregate=Sum("action_amount"))
            .values("aggregate")
        )
        return queryset.annotate(
            action_aggregate=Subquery(aggregate_clause),
            itemized=self.get_itemization_clause(),
        )

    def get_itemization_clause(self):
        over_two_hundred_types = (
            schedule_a_over_two_hundred_types  # + schedule_b_over_two_hundred_types
        )
        return Case(
            When(action_aggregate__lt=Value(Decimal(0)), then=Value(True)),
            When(
                transaction_type_identifier__in=over_two_hundred_types,
                then=Q(action_aggregate__gt=Value(Decimal(200))),
            ),
            default=Value(True),
            output_field=BooleanField(),
        )
