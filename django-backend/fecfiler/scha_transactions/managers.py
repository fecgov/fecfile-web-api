from decimal import Decimal
from fecfiler.soft_delete.managers import SoftDeleteManager
from django.db.models import OuterRef, Subquery, Sum, Q, Case, When, Value, BooleanField

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
        group_clause = Q(aggregation_group=OuterRef("aggregation_group"))

        aggregate_clause = (
            queryset.filter(contact_clause, year_clause, date_clause, group_clause)
            .values("committee_account_id")
            .annotate(aggregate=Sum("contribution_amount"))
            .values("aggregate")
        )
        return (
            super()
            .get_queryset()
            .annotate(
                contribution_aggregate=Subquery(aggregate_clause),
                itemized=self.get_itemization_clause(),
            )
        )

    def get_itemization_clause(self):
        over_two_hundred_types = [
            "INDIVIDUAL_RECEIPT",
            "INDIVIDUAL_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO",
            "INDIVIDUAL_RECOUNT_RECEIPT",
            "JF_TRANSFER_NATIONAL_PARTY_CONVENTION_ACCOUNT",
            "JF_TRANSFER_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT",
            "OFFSET_TO_OPERATING_EXPENDITURES",
            "OTHER_COMMITTEE_NON_CONTRIBUTION_ACCOUNT",
            "OTHER_RECEIPT",
            "TRIBAL_RECEIPT",
            "TRIBAL_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO",
            "TRIBAL_RECOUNT_RECEIPT",
            "PAC_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO",
            "PAC_NATIONAL_PARTY_RECOUNT_ACCOUNT",
            "PAC_RECOUNT_RECEIPT",
            "PARTY_RECOUNT_RECEIPT",
            "BUSINESS_LABOR_NON_CONTRIBUTION_ACCOUNT",
            "JF_TRANSFER_NATIONAL_PARTY_RECOUNT_ACCOUNT",
            "PAC_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO",
            "INDIVIDUAL_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO",
            "TRIBAL_NATIONAL_PARTY_RECOUNT_JF_TRANSFER_MEMO",
            "INDIVIDUAL_RECEIPT_NON_CONTRIBUTION_ACCOUNT",
            "INDIVIDUAL_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT",
            "PAC_NATIONAL_PARTY_CONVENTION_ACCOUNT",
            "PAC_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT",
            "PARTY_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT",
            "TRIBAL_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT",
            "TRIBAL_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO",
            "TRIBAL_NATIONAL_PARTY_CONVENTION_ACCOUNT",
            "INDIVIDUAL_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO",
            "PAC_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO",
            "PARTY_NATIONAL_PARTY_RECOUNT_ACCOUNT",
            "INDIVIDUAL_NATIONAL_PARTY_RECOUNT_ACCOUNT",
            "INDIVIDUAL_NATIONAL_PARTY_CONVENTION_ACCOUNT",
            "PARTY_NATIONAL_PARTY_CONVENTION_ACCOUNT",
            "TRIBAL_NATIONAL_PARTY_RECOUNT_ACCOUNT",
            "UNREGISTERED_RECEIPT_FROM_PERSON",
            "PARTNERSHIP_RECEIPT",
            "PARTNERSHIP_MEMO",
        ]
        return Case(
            When(contribution_aggregate__lt=Value(Decimal(0)), then=Value(True)),
            When(
                transaction_type_identifier__in=over_two_hundred_types,
                then=Q(contribution_aggregate__gt=Value(Decimal(200))),
            ),
            default=Value(True),
            output_field=BooleanField(),
        )
