from fecfiler.soft_delete.managers import SoftDeleteManager
from fecfiler.transactions.schedule_a.managers import (
    over_two_hundred_types as schedule_a_over_two_hundred_types,
)
from fecfiler.transactions.schedule_b.managers import (
    over_two_hundred_types as schedule_b_over_two_hundred_types,
)
from django.db.models.functions import Coalesce, Concat
from django.db.models import (
    OuterRef,
    Subquery,
    Sum,
    Q,
    F,
    Case,
    When,
    Value,
    BooleanField,
    TextField,
    DecimalField,
)
from decimal import Decimal
from enum import Enum
from .schedule_b.managers import refunds as schedule_b_refunds

"""Manager to deterimine fields that are used the same way across transactions,
but are called different names"""


class TransactionManager(SoftDeleteManager):
    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .annotate(
                schedule=Case(
                    When(schedule_a__isnull=False, then=Schedule.A.value),
                    When(schedule_b__isnull=False, then=Schedule.B.value),
                    When(schedule_c__isnull=False, then=Schedule.C.value),
                    When(schedule_c1__isnull=False, then=Schedule.C1.value),
                    When(schedule_c1__isnull=False, then=Schedule.C2.value),
                    When(schedule_d__isnull=False, then=Schedule.D.value),
                    When(schedule_e__isnull=False, then=Schedule.E.value)
                ),
                date=Coalesce(
                    "schedule_a__contribution_date",
                    "schedule_b__expenditure_date",
                    "schedule_c__loan_incurred_date",
                ),
                amount=Coalesce(
                    "schedule_a__contribution_amount",
                    "schedule_b__expenditure_amount",
                    "schedule_c__loan_amount",
                ),
                effective_amount=self.get_amount_clause(),
            ).alias(
                parent_schedule=Case(
                    When(parent_transaction__schedule_a__isnull=False, then=Schedule.A.value),
                    When(parent_transaction__schedule_b__isnull=False, then=Schedule.B.value),
                    When(parent_transaction__schedule_c__isnull=False, then=Schedule.C.value),
                    When(parent_transaction__schedule_c1__isnull=False, then=Schedule.C1.value),
                    When(parent_transaction__schedule_c1__isnull=False, then=Schedule.C2.value),
                    When(parent_transaction__schedule_d__isnull=False, then=Schedule.D.value),
                    When(parent_transaction__schedule_e__isnull=False, then=Schedule.E.value)
                ),
                grandparent_schedule=Case(
                    When(parent_transaction__parent_transaction__schedule_a__isnull=False, then=Schedule.A.value),
                    When(parent_transaction__parent_transaction__schedule_b__isnull=False, then=Schedule.B.value),
                    When(parent_transaction__parent_transaction__schedule_c__isnull=False, then=Schedule.C.value),
                    When(parent_transaction__parent_transaction__schedule_c1__isnull=False, then=Schedule.C1.value),
                    When(parent_transaction__parent_transaction__schedule_c1__isnull=False, then=Schedule.C2.value),
                    When(parent_transaction__parent_transaction__schedule_d__isnull=False, then=Schedule.D.value),
                    When(parent_transaction__parent_transaction__schedule_e__isnull=False, then=Schedule.E.value)
                ),
                parent_date=Coalesce(
                    "parent_transaction__schedule_a__contribution_date",
                    "parent_transaction__schedule_b__expenditure_date",
                    "parent_transaction__schedule_c__loan_incurred_date",
                ),
                grandparent_date=Coalesce(
                    "parent_transaction__parent_transaction__schedule_a__contribution_date",
                    "parent_transaction__parent_transaction__schedule_b__expenditure_date",
                    "parent_transaction__parent_transaction__schedule_c__loan_incurred_date",
                ),
                parent_amount=Coalesce(
                    "parent_transaction__schedule_a__contribution_amount",
                    "parent_transaction__schedule_b__expenditure_amount",
                    "parent_transaction__schedule_c__loan_amount",
                ),
                grandparent_amount=Coalesce(
                    "parent_transaction__parent_transaction__schedule_a__contribution_amount",
                    "parent_transaction__parent_transaction__schedule_b__expenditure_amount",
                    "parent_transaction__parent_transaction__schedule_c__loan_amount",
                ),
            ).alias(
                parent_effective_amount=self.get_parent_amount_clause(),
                grandparent_effective_amount=self.get_grandparent_amount_clause(),
            )
        )

        contact_clause = Q(contact_1_id=OuterRef("contact_1_id"))
        year_clause = Q(date__year=OuterRef("date__year"))
        date_clause = Q(date__lt=OuterRef("date")) | Q(
            date=OuterRef("date"), created__lte=OuterRef("created")
        )
        group_clause = Q(aggregation_group=OuterRef("aggregation_group"))
        aggregate_clause = (
            queryset.filter(contact_clause, year_clause, date_clause, group_clause)
            .values("committee_account_id")
            .annotate(aggregate=Sum("effective_amount"))
            .values("aggregate")
        )

        parent_contact_clause = Q(contact_1_id=OuterRef("parent_transaction__contact_1_id"))
        parent_year_clause = Q(parent_date__year=OuterRef("parent_date__year"))
        parent_date_clause = Q(parent_date__lt=OuterRef("parent_date")) | Q(
            parent_date=OuterRef("parent_date"), created__lte=OuterRef("parent_transaction__created")
        )
        parent_group_clause = Q(aggregation_group=OuterRef("parent_transaction__aggregation_group"))
        parent_aggregate_clause = (
            queryset.filter(parent_contact_clause, parent_year_clause, parent_date_clause, parent_group_clause)
            .values("parent_transaction__committee_account_id")
            .annotate(parent_aggregate=Sum("parent_effective_amount"))
            .values("parent_aggregate")
        )

        grandparent_contact_clause = Q(contact_1_id=OuterRef("parent_transaction__parent_transaction__contact_1_id"))
        grandparent_year_clause = Q(grandparent_date__year=OuterRef("grandparent_date__year"))
        grandparent_date_clause = Q(grandparent_date__lt=OuterRef("grandparent_date")) | Q(
            grandparent_date=OuterRef("grandparent_date"), created__lte=OuterRef("parent_transaction__parent_transaction__created")
        )
        grandparent_group_clause = Q(aggregation_group=OuterRef("parent_transaction__parent_transaction__aggregation_group"))
        grandparent_aggregate_clause = (
            queryset.filter(grandparent_contact_clause, grandparent_year_clause, grandparent_date_clause, grandparent_group_clause)
            .values("parent_transaction__parent_transaction__committee_account_id")
            .annotate(grandparent_aggregate=Sum("grandparent_effective_amount"))
            .values("grandparent_aggregate")
        )

        return (
            queryset.annotate(
                aggregate=Subquery(aggregate_clause)
            ).alias(
                parent_aggregate=Subquery(parent_aggregate_clause),
                grandparent_aggregate=Subquery(grandparent_aggregate_clause),
            ).annotate(
                itemized=self.get_itemization_clause()
            )
            .annotate(
                form_type=Case(
                    When(_form_type="SA11AI", itemized=False, then=Value("SA11AII")),
                    When(_form_type="SA11AII", itemized=True, then=Value("SA11AI")),
                    default=F("_form_type"),
                    output_field=TextField(),
                )
            )
            .alias(
                order_key=Case(
                    When(
                        parent_transaction__isnull=False,
                        then=Concat(
                            Case(
                                When(
                                    parent_transaction__schedule_a__isnull=False,
                                    then=Schedule.A.value,
                                ),
                                When(
                                    parent_transaction__schedule_b__isnull=False,
                                    then=Schedule.B.value,
                                ),
                            ),
                            "parent_transaction___form_type",
                            "parent_transaction__created",
                            "schedule",
                            "_form_type",
                            "created",
                            output_field=TextField(),
                        ),
                    ),
                    default=Concat(
                        "schedule", "_form_type", "created", output_field=TextField()
                    ),
                    output_field=TextField(),
                ),
            )
            .order_by("order_key")
        )

    def get_itemization_clause(self):
        over_two_hundred_types = (
            schedule_a_over_two_hundred_types + schedule_b_over_two_hundred_types
        )

        return Case(
            # No parent
            When(parent_transaction__isnull=True, then=Case(
                When(force_itemized__isnull=False, then=F("force_itemized")),
                When(aggregate__lt=Value(Decimal(0)), then=Value(True)),
                When(
                    transaction_type_identifier__in=over_two_hundred_types,
                    then=Q(aggregate__gt=Value(Decimal(200))),
                ),
                default=Value(True),
                output_field=BooleanField()
            )),
            When(parent_transaction__isnull=False, then=Case(
                # Parent
                When(parent_transaction__parent_transaction__isnull=True, then=Case(
                    When(parent_transaction__force_itemized__isnull=False, then=F("parent_transaction__force_itemized")),
                    When(parent_aggregate__lt=Value(Decimal(0)), then=Value(True)),
                    When(
                        parent_transaction__transaction_type_identifier__in=over_two_hundred_types,
                        then=Q(parent_aggregate__gt=Value(Decimal(200))),
                    ),
                    default=Value(True),
                    output_field=BooleanField()
                )),
                # Grandparent
                When(parent_transaction__parent_transaction__isnull=False, then=Case(
                    When(parent_transaction__parent_transaction__force_itemized__isnull=False, then=F("parent_transaction__parent_transaction__force_itemized")),
                    When(grandparent_aggregate__lt=Value(Decimal(0)), then=Value(True)),
                    When(
                        parent_transaction__parent_transaction__transaction_type_identifier__in=over_two_hundred_types,
                        then=Q(grandparent_aggregate__gt=Value(Decimal(200))),
                    ),
                    default=Value(True),
                    output_field=BooleanField()
                ))
            )),
            default=Value(True),
            output_field=BooleanField()
        )

    def get_amount_clause(self):
        return Case(
            When(
                transaction_type_identifier__in=schedule_b_refunds,
                then=F("amount") * Value(Decimal(-1)),
            ),
            default="amount",
            output_field=DecimalField(),
        )

    def get_parent_amount_clause(self):
        return Case(
            When(
                parent_transaction__transaction_type_identifier__in=schedule_b_refunds,
                then=F("parent_amount") * Value(Decimal(-1)),
            ),
            default="parent_amount",
            output_field=DecimalField(),
        )

    def get_grandparent_amount_clause(self):
        return Case(
            When(
                parent_transaction__parent_transaction__transaction_type_identifier__in=schedule_b_refunds,
                then=F("grandparent_amount") * Value(Decimal(-1)),
            ),
            default="grandparent_amount",
            output_field=DecimalField(),
        )


class Schedule(Enum):
    A = Value("A")
    B = Value("B")
    C = Value("C")
    C2 = Value("C1")
    C1 = Value("C2")
    D = Value("D")
    E = Value("E")
