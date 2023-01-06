from decimal import Decimal
from fecfiler.soft_delete.managers import SoftDeleteManager
from django.db.models import OuterRef, Subquery, Sum, Q, Case, When, Value, BooleanField

"""Manager to calculate contribution_aggregate just-in-time"""


class ScheduleBTransactionManager(SoftDeleteManager):
    def get_queryset(self):
        queryset = super().get_queryset()

        contact_clause = Q(contact_id=OuterRef("contact_id"))
        year_clause = Q(contribution_date__year=OuterRef("expenditure_date__year"))
        date_clause = Q(contribution_date__lt=OuterRef("expenditure_date")) | Q(
            contribution_date=OuterRef("expenditure_date"),
            created__lte=OuterRef("created"),
        )
        group_clause = Q(aggregation_group=OuterRef("aggregation_group"))

        aggregate_clause = (
            queryset.filter(contact_clause, year_clause, date_clause, group_clause)
            .values("committee_account_id")
            .annotate(aggregate=Sum("expenditure_amount"))
            .values("aggregate")
        )
        return (
            super()
            .get_queryset()
            .annotate(
                expenditure_aggregate=Subquery(aggregate_clause),
                itemized=self.get_itemization_clause(),
            )
        )

    def get_itemization_clause(self):
        over_two_hundred_types = []
        return Case(
            When(expenditure_aggregate__lt=Value(Decimal(0)), then=Value(True)),
            When(
                transaction_type_identifier__in=over_two_hundred_types,
                then=Q(expenditure_aggregate__gt=Value(Decimal(200))),
            ),
            default=Value(True),
            output_field=BooleanField(),
        )
