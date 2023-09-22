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
                    When(schedule_c2__isnull=False, then=Schedule.C2.value),
                    When(schedule_d__isnull=False, then=Schedule.D.value),
                    When(schedule_e__isnull=False, then=Schedule.E.value),
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
                    "schedule_c2__guaranteed_amount",
                ),
                effective_amount=self.get_amount_clause(),
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

        loan_payment_to_date_clause = (
            queryset.filter(
                parent_transaction_id=OuterRef("id"),
                transaction_type_identifier__in=[
                    "LOAN_REPAYMENT_RECEIVED",
                    "LOAN_REPAYMENT_MADE",
                ],
            )
            .values("committee_account_id")
            .annotate(payment_to_date=Sum("amount"))
            .values("payment_to_date")
        )

        debt_payment_clause = (
            queryset.filter(debt_id=OuterRef("id"))
            .values("committee_account_id")
            .annotate(payment_to_date=Sum("amount"))
            .values("payment_to_date")
        )
        return (
            queryset.annotate(
                aggregate=Subquery(aggregate_clause),
                loan_payment_to_date=Case(
                    When(
                        schedule_c__isnull=False,
                        then=Coalesce(
                            Subquery(loan_payment_to_date_clause), Value(Decimal(0))
                        ),
                    ),
                    default=Value(Decimal(0)),
                ),
                payment_amount=Case(  # debt payment
                    When(
                        schedule_d__isnull=False,
                        then=Coalesce(Subquery(debt_payment_clause), Value(Decimal(0))),
                    ),
                    default=Value(Decimal(0)),
                ),
                itemized=self.get_itemization_clause(),
            )
            .annotate(
                loan_balance=F("amount") - F("loan_payment_to_date"),
                form_type=Case(
                    When(_form_type="SA11AI", itemized=False, then=Value("SA11AII")),
                    When(_form_type="SA11AII", itemized=True, then=Value("SA11AI")),
                    When(
                        transaction_type_identifier="C2_LOAN_GUARANTOR",
                        parent_transaction__transaction_type_identifier=(
                            "LOAN_BY_COMMITTEE"
                        ),
                        then=Value("SC2/9"),
                    ),
                    When(
                        transaction_type_identifier="C2_LOAN_GUARANTOR",
                        then=Value("SC2/10"),
                    ),
                    default=F("_form_type"),
                    output_field=TextField(),
                ),
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
            When(force_itemized__isnull=False, then=F("force_itemized")),
            When(aggregate__lt=Value(Decimal(0)), then=Value(True)),
            When(
                transaction_type_identifier__in=over_two_hundred_types,
                then=Q(aggregate__gt=Value(Decimal(200))),
            ),
            default=Value(True),
            output_field=BooleanField(),
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


class Schedule(Enum):
    A = Value("A")
    B = Value("B")
    C = Value("C")
    C2 = Value("C1")
    C1 = Value("C2")
    D = Value("D")
    E = Value("E")
