from datetime import datetime
from fecfiler.soft_delete.managers import SoftDeleteManager
from django.db.models import OuterRef, Subquery, Sum, F, Q
from django.db import models

"""Manager to calculate contribution_aggregate just-in-time"""


class SchATransactionManager(SoftDeleteManager):
    def get_queryset(self):
        queryset = super().get_queryset()

        contact_clause = Q(contact_id=OuterRef("contact_id"))
        year_clause = Q(contribution_date__year=OuterRef("contribution_date__year"))
        date_clause = Q(contribution_date__lt=OuterRef("contribution_date")) | Q(
            contribution_date=OuterRef("contribution_date"),
            created__lte=OuterRef("created"),
        )

        aggregate_clause = (
            queryset.filter(
                contact_clause,
                year_clause,
                date_clause
                # aggregation_group=OuterRef("aggregation_group")
            )
            .values("committee_account_id")
            .annotate(aggregate=Sum("contribution_amount"))
            .values("aggregate")
        )
        return (
            super()
            .get_queryset()
            .annotate(contribution_aggregate=Subquery(aggregate_clause))
        )
