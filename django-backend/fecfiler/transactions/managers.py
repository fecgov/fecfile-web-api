from fecfiler.soft_delete.managers import SoftDeleteManager
from fecfiler.transactions.schedule_a.managers import (
    over_two_hundred_types as schedule_a_over_two_hundred_types,
)
from fecfiler.transactions.schedule_b.managers import (
    over_two_hundred_types as schedule_b_over_two_hundred_types,
)
from fecfiler.transactions.schedule_e.managers import (
    over_two_hundred_types as schedule_e_over_two_hundred_types,
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
    UUIDField,
    ExpressionWrapper
)
from decimal import Decimal
from enum import Enum
from .schedule_b.managers import refunds as schedule_b_refunds
from fecfiler.contacts.models import Contact

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
                    "schedule_e__disbursement_date",
                    "schedule_e__dissemination_date"
                ),
                amount=Coalesce(
                    "schedule_a__contribution_amount",
                    "schedule_b__expenditure_amount",
                    "schedule_c__loan_amount",
                    "schedule_c2__guaranteed_amount",
                    "debt__schedule_d__incurred_amount",
                    "schedule_d__incurred_amount",
                    "schedule_e__expenditure_amount",
                ),
                effective_amount=self.get_amount_clause(),
                candidate_contact_id=self.get_candidate_contact_clause(),
            )
        )

        primary_contact_clause = Q(contact_1_id=OuterRef("contact_1_id"))
        election_clause = (
            Q(
                schedule_e__isnull=False
            ) & Q(
                schedule_e__election_code=OuterRef(
                    "schedule_e__election_code"
                )
            ) & Q(
                schedule_e__so_candidate_office=OuterRef(
                    "schedule_e__so_candidate_office"
                )
            ) & Q(
                Q(
                    schedule_e__so_candidate_state=OuterRef(
                        "schedule_e__so_candidate_state"
                    )
                ) | (
                    Q(schedule_e__so_candidate_office__isnull=True)
                    & Q(outer_candidate_state__isnull=True)
                )
            ) & (
                Q(
                    schedule_e__so_candidate_district=OuterRef(
                        "schedule_e__so_candidate_district"
                    )
                ) | (
                    Q(schedule_e__so_candidate_district__isnull=True)
                    & Q(outer_candidate_district__isnull=True)
                )
            )
        )
        year_clause = Q(date__year=OuterRef("date__year"))
        date_clause = Q(date__lt=OuterRef("date")) | Q(
            date=OuterRef("date"), created__lte=OuterRef("created")
        )
        group_clause = Q(aggregation_group=OuterRef("aggregation_group"))
        force_unaggregated_clause = ~Q(force_unaggregated=True)

        aggregate_clause = (
            queryset.filter(
                primary_contact_clause,
                year_clause,
                date_clause,
                group_clause,
                force_unaggregated_clause,
            )
            .values("committee_account_id")
            .annotate(aggregate=Sum("effective_amount"))
            .values("aggregate")
        )
        calendar_ytd_clause = (
            queryset.alias(  # Needed to get around null-matching bug with Q()
                outer_candidate_district=ExpressionWrapper(
                    OuterRef('schedule_e__so_candidate_district'),
                    output_field=TextField()
                ),
                outer_candidate_state=ExpressionWrapper(
                    OuterRef('schedule_e__so_candidate_state'),
                    output_field=TextField()
                )
            ).filter(
                election_clause,
                year_clause,
                date_clause,
                group_clause,
            )
            .values("committee_account_id")
            .annotate(calendar_ytd=Sum("effective_amount"))
            .values("calendar_ytd")
        )

        loan_payment_to_date_clause = (
            queryset.filter(
                loan__transaction_id=OuterRef("transaction_id"),
                transaction_type_identifier__in=[
                    "LOAN_REPAYMENT_RECEIVED",
                    "LOAN_REPAYMENT_MADE",
                ],
                report__coverage_through_date__lte=OuterRef(
                    "report__coverage_through_date"
                ),
            )
            .values("committee_account_id")
            .annotate(payment_to_date=Sum("amount"))
            .values("payment_to_date")
        )

        debt_payment_clause = (
            queryset.filter(debt_id=OuterRef("id"), schedule_d__isnull=True)
            .values("committee_account_id")
            .annotate(payment_to_date=Sum("amount"))
            .values("payment_to_date")
        )
        incurred_prior_clause = (
            queryset.filter(
                ~Q(debt_id=OuterRef("id")),
                transaction_id=OuterRef("transaction_id"),
                report__coverage_through_date__lt=OuterRef(
                    "report__coverage_from_date"
                ),
            )
            .values("committee_account_id")
            .annotate(incurred_prior=Sum("schedule_d__incurred_amount"),)
            .values("incurred_prior")
        )
        debt_payments_prior_clause = (
            queryset.filter(
                ~Q(debt_id=OuterRef("id")),
                debt__transaction_id=OuterRef("transaction_id"),
                schedule_d__isnull=True,
                date__lt=OuterRef("report__coverage_from_date"),
            )
            .values("committee_account_id")
            .annotate(debt_payments_prior=Sum("amount"))
            .values("debt_payments_prior")
        )
        return (
            queryset.annotate(
                aggregate=Coalesce(Subquery(aggregate_clause), Value(Decimal(0))),
                calendar_ytd=Coalesce(Subquery(calendar_ytd_clause), Value(Decimal(0))),
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
                payment_prior=Case(  # debt payments
                    When(
                        schedule_d__isnull=False,
                        then=Coalesce(
                            Subquery(debt_payments_prior_clause), Value(Decimal(0))
                        ),
                    ),
                    default=Value(Decimal(0)),
                ),
                incurred_prior=Case(
                    When(
                        schedule_d__isnull=False,
                        then=Coalesce(
                            Subquery(incurred_prior_clause), Value(Decimal(0))
                        ),
                    ),
                    default=Value(Decimal(0)),
                ),
                itemized=self.get_itemization_clause(),
            )
            .annotate(
                loan_balance=F("amount") - F("loan_payment_to_date"),
                beginning_balance=F("incurred_prior") - F("payment_prior"),
                balance_at_close=Case(
                    When(
                        schedule_d__isnull=False,
                        then=F("beginning_balance")
                        + F("schedule_d__incurred_amount")
                        - F("payment_amount"),
                    ),
                ),
                form_type=Case(
                    When(_form_type="SA11AI", itemized=False, then=Value("SA11AII")),
                    When(_form_type="SA11AII", itemized=True, then=Value("SA11AI")),
                    When(
                        transaction_type_identifier="C2_LOAN_GUARANTOR",
                        loan__transaction_type_identifier=("LOAN_BY_COMMITTEE"),
                        then=Value("SC2/9"),
                    ),
                    When(
                        transaction_type_identifier="C2_LOAN_GUARANTOR",
                        then=Value("SC2/10"),
                    ),
                    default=F("_form_type"),
                    output_field=TextField(),
                ),
                back_reference_tran_id_number=Coalesce(
                    F("parent_transaction__transaction_id"),
                    F("debt__transaction_id"),
                    F("loan__transaction_id"),
                    Value(None),
                ),
                back_reference_sched_name=Coalesce(
                    F("parent_transaction___form_type"),
                    F("debt___form_type"),
                    F("loan___form_type"),
                    Value(None),
                ),
            )
            .annotate(
                balance=Coalesce(
                    F("balance_at_close"), F("loan_balance"), Value(Decimal(0.0))
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
            schedule_a_over_two_hundred_types
            + schedule_b_over_two_hundred_types
            + schedule_e_over_two_hundred_types
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

    def get_candidate_contact_clause(self):
        return Case(
            When(
                contact_2__type=Contact.ContactType.CANDIDATE,
                then=F("contact_2_id")
            ),
            When(
                contact_3__type=Contact.ContactType.CANDIDATE,
                then=F("contact_3_id")
            ),
            default=None,
            output_field=UUIDField()
        )


class Schedule(Enum):
    A = Value("A")
    B = Value("B")
    C = Value("C")
    C2 = Value("C1")
    C1 = Value("C2")
    D = Value("D")
    E = Value("E")
