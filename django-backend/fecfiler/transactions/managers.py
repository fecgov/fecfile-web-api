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
from django.db.models.functions import Coalesce, Concat, Lag
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
    ExpressionWrapper,
    RowRange,
    Window,
    Manager,
)
from django.db.models.expressions import RawSQL
from django.contrib.postgres.expressions import ArraySubquery
from decimal import Decimal
from enum import Enum
from .schedule_b.managers import refunds as schedule_b_refunds

"""Manager to deterimine fields that are used the same way across transactions,
but are called different names"""


class TransactionManager(SoftDeleteManager):
    entity_aggregate_window = {
        "partition_by": [
            F("contact_1_id"),
            F("date__year"),
            F("aggregation_group"),
        ],
        "order_by": ["date", "created"],
        "frame": RowRange(None, 0),
    }
    election_aggregate_window = {
        "partition_by": [
            F("schedule_e__election_code"),
            F("contact_2__candidate_office"),
            F("contact_2__candidate_state"),
            F("contact_2__candidate_district"),
            F("date__year"),
            F("aggregation_group"),
        ],
        "order_by": ["date", "created"],
        "frame": RowRange(None, 0),
    }
    loan_payment_window = {
        "partition_by": [F("debt_id")],
        "order_by": ["loan_key"],
        "frame": RowRange(None, 0),
    }
    debt_payment_window = {
        "partition_by": [F("debt_id")],
        "order_by": ["debt_key"],
        "frame": RowRange(None, 0),
    }

    def get_queryset(self):
        return super().get_queryset()

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
                    "schedule_e__dissemination_date",
                ),
                amount=Coalesce(
                    "schedule_a__contribution_amount",
                    "schedule_b__expenditure_amount",
                    "schedule_c__loan_amount",
                    "schedule_c2__guaranteed_amount",
                    "schedule_d__incurred_amount",
                    "schedule_e__expenditure_amount",
                ),
                effective_amount=self.EFFECTIVE_AMOUNT_CLAUSE(),
                debt_incurred_amount=Case(
                    When(
                        schedule_d__isnull=False,
                        debt__isnull=False,
                        then=F("debt__schedule_d__incurred_amount"),
                    ),
                    default=F("amount"),
                ),
            )
        )
        primary_contact_clause = Q(contact_1_id=OuterRef("contact_1_id"))

        election_clause = (
            Q(schedule_e__isnull=False)
            & Q(parent_transaction__isnull=True)
            & Q(schedule_e__election_code=OuterRef("schedule_e__election_code"))
            & Q(contact_2__candidate_office=OuterRef("contact_2__candidate_office"))
            & Q(
                Q(contact_2__candidate_state=OuterRef("contact_2__candidate_state"))
                | (
                    Q(contact_2__candidate_state__isnull=True)
                    & Q(outer_candidate_state__isnull=True)
                )
            )
            & (
                Q(
                    contact_2__candidate_district=OuterRef(
                        "contact_2__candidate_district"
                    )
                )
                | (
                    Q(contact_2__candidate_district__isnull=True)
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

        calendar_ytd_per_election_office_clause = (
            queryset.alias(  # Needed to get around null-matching bug with Q()
                outer_candidate_district=ExpressionWrapper(
                    OuterRef("contact_2__candidate_district"),
                    output_field=TextField(),
                ),
                outer_candidate_state=ExpressionWrapper(
                    OuterRef("contact_2__candidate_state"), output_field=TextField()
                ),
            )
            .filter(
                election_clause,
                year_clause,
                date_clause,
                group_clause,
                force_unaggregated_clause,
            )
            .values("committee_account_id")
            .annotate(calendar_ytd_per_election_office=Sum("effective_amount"))
            .values("calendar_ytd_per_election_office")
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
            .annotate(
                incurred_prior=Sum("schedule_d__incurred_amount"),
            )
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
                calendar_ytd_per_election_office=Coalesce(
                    Subquery(calendar_ytd_per_election_office_clause), Value(Decimal(0))
                ),
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
                itemized=self.ITEMIZATION_CLAUSE(),
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
                    F("reatt_redes__transaction_id"),
                    F("parent_transaction__transaction_id"),
                    F("debt__transaction_id"),
                    F("loan__transaction_id"),
                    Value(None),
                ),
                back_reference_sched_name=Coalesce(
                    F("reatt_redes___form_type"),
                    F("parent_transaction___form_type"),
                    F("debt___form_type"),
                    F("loan___form_type"),
                    Value(None),
                ),
                line_label=Case(
                    # Schedule A
                    When(_form_type="SA11A", then=Value("11(a)")),
                    When(_form_type="SA11AI", itemized=True, then=Value("11(a)(i)")),
                    When(_form_type="SA11AI", itemized=False, then=Value("11(a)(ii)")),
                    When(_form_type="SA11AII", itemized=False, then=Value("11(a)(ii)")),
                    When(_form_type="SA11AII", itemized=True, then=Value("11(a)(i)")),
                    When(_form_type="SA11B", then=Value("11(b)")),
                    When(_form_type="SA11C", then=Value("11(c)")),
                    When(_form_type="SA12", then=Value("12")),
                    When(_form_type="SA13", then=Value("13")),
                    When(_form_type="SA14", then=Value("14")),
                    When(_form_type="SA15", then=Value("15")),
                    When(_form_type="SA16", then=Value("16")),
                    When(_form_type="SA17", then=Value("17")),
                    # Schedule B
                    When(_form_type="SB21B", then=Value("21(b)")),
                    When(_form_type="SB22", then=Value("22")),
                    When(_form_type="SB23", then=Value("23")),
                    When(_form_type="SB26", then=Value("26")),
                    When(_form_type="SB27", then=Value("27")),
                    When(_form_type="SB28A", then=Value("28(a)")),
                    When(_form_type="SB28B", then=Value("28(b)")),
                    When(_form_type="SB28C", then=Value("28(c)")),
                    When(_form_type="SB29", then=Value("29")),
                    When(_form_type="SB30B", then=Value("30(b)")),
                    # Schedule C
                    When(_form_type="SC/10", then=Value("10")),
                    When(_form_type="SC/9", then=Value("9")),
                    # Schedule D
                    When(_form_type="SD9", then=Value("9")),
                    When(_form_type="SD10", then=Value("10")),
                    # Schedule E
                    When(_form_type="SE", then=Value("24")),
                ),
                line_label_order_key=Case(
                    # Schedule A
                    When(_form_type="SA11A", then=Value(3)),
                    When(_form_type="SA11AI", itemized=True, then=Value(4)),
                    When(_form_type="SA11AI", itemized=False, then=Value(5)),
                    When(_form_type="SA11AII", itemized=False, then=Value(5)),
                    When(_form_type="SA11AII", itemized=True, then=Value(4)),
                    When(_form_type="SA11B", then=Value(6)),
                    When(_form_type="SA11C", then=Value(7)),
                    When(_form_type="SA12", then=Value(8)),
                    When(_form_type="SA13", then=Value(9)),
                    When(_form_type="SA14", then=Value(10)),
                    When(_form_type="SA15", then=Value(11)),
                    When(_form_type="SA16", then=Value(12)),
                    When(_form_type="SA17", then=Value(13)),
                    # Schedule B
                    When(_form_type="SB21B", then=Value(14)),
                    When(_form_type="SB22", then=Value(15)),
                    When(_form_type="SB23", then=Value(16)),
                    When(_form_type="SB26", then=Value(18)),
                    When(_form_type="SB27", then=Value(19)),
                    When(_form_type="SB28A", then=Value(20)),
                    When(_form_type="SB28B", then=Value(21)),
                    When(_form_type="SB28C", then=Value(22)),
                    When(_form_type="SB29", then=Value(23)),
                    When(_form_type="SB30B", then=Value(24)),
                    # Schedule C
                    When(_form_type="SC/10", then=Value(2)),
                    When(_form_type="SC/9", then=Value(1)),
                    # Schedule D
                    When(_form_type="SD9", then=Value(1)),
                    When(_form_type="SD10", then=Value(2)),
                    # Schedule E
                    When(_form_type="SE", then=Value(17)),
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

    def ITEMIZATION_CLAUSE(self):
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

    EFFECTIVE_AMOUNT_CLAUSE = Case(
        When(
            transaction_type_identifier__in=schedule_b_refunds,
            then=F("amount") * Value(Decimal(-1)),
        ),
        default="amount",
        output_field=DecimalField(),
    )

    def SCHEDULE_CLAUSE(self):
        return Case(
            When(schedule_a__isnull=False, then=Schedule.A.value),
            When(schedule_b__isnull=False, then=Schedule.B.value),
            When(schedule_c__isnull=False, then=Schedule.C.value),
            When(schedule_c1__isnull=False, then=Schedule.C1.value),
            When(schedule_c2__isnull=False, then=Schedule.C2.value),
            When(schedule_d__isnull=False, then=Schedule.D.value),
            When(schedule_e__isnull=False, then=Schedule.E.value),
        )

    DATE_CLAUSE = Coalesce(
        "schedule_a__contribution_date",
        "schedule_b__expenditure_date",
        "schedule_c__loan_incurred_date",
        "schedule_e__disbursement_date",
        "schedule_e__dissemination_date",
    )

    AMOUNT_CLAUSE = Coalesce(
        "schedule_a__contribution_amount",
        "schedule_b__expenditure_amount",
        "schedule_c__loan_amount",
        "schedule_c2__guaranteed_amount",
        "debt__schedule_d__incurred_amount",
        "schedule_d__incurred_amount",
        "schedule_e__expenditure_amount",
    )

    def ENTITY_AGGREGGATE_CLAUSE(self):
        return Window(
            expression=Sum("effective_amount"), **self.entity_aggregate_window
        ) - Case(
            When(force_unaggregated=True, then=F("effective_amount")),
            default=Value(0.0),
            output_field=DecimalField(),
        )

    def ELECTION_AGGREGATE_CLAUSE(self):
        return Window(
            expression=Sum("effective_amount"), **self.election_aggregate_window
        ) - Case(
            When(force_unaggregated=True, then=F("effective_amount")),
            default=Value(0.0),
            output_field=DecimalField(),
        )

    def BACK_REFERENCE_CLAUSE(self):
        return Coalesce(
            F("reatt_redes__transaction_id"),
            F("parent_transaction__transaction_id"),
            F("debt__transaction_id"),
            F("loan__transaction_id"),
            Value(None),
        )

    # clause used to facilitate sorting on name as it's displayed
    DISPLAY_NAME_CLAUSE = Coalesce(
        "contact_1__name",
        Concat(
            "contact_1__last_name",
            Value("', '"),
            "contact_2__last_name",
            output_field=TextField(),
        ),
    )

    def LOAN_KEY_CLAUSE(self):
        return Case(
            When(
                Q(loan_id__isnull=False)
                & Q(
                    schedule__in=[
                        Schedule.A.value,
                        Schedule.B.value,
                        Schedule.E.value,
                    ]
                )
                & Q(
                    transaction_type_identifier__in=[
                        "'LOAN_REPAYMENT_RECEIVED'",
                        "'LOAN_REPAYMENT_MADE'",
                    ]
                ),
                then=Concat(F("loan__transaction_id"), F("date")),
            ),
            When(
                schedule_c__isnull=False,
                then=Concat(F("transaction_id"), F("report__coverage_from_date")),
            ),
            default=None,
            output_field=TextField(),
        )

    def LOAN_PAYMENT_CLAUSE(self):
        return Window(
            expression=Sum("effective_amount"), **self.loan_payment_window
        ) - Case(
            When(
                schedule_c__isnull=False,
                then=F("effective_amount"),
            ),
            default=Value(0.0),
            output_field=DecimalField(),
        )

    def INCURRED_PRIOR_CLAUSE(self):
        return Case(
            When(
                schedule_d__isnull=False,
                then=Coalesce(
                    Subquery(
                        (
                            super()
                            .get_queryset()
                            .filter(
                                ~Q(debt_id=OuterRef("id")),
                                transaction_id=OuterRef("transaction_id"),
                                report__coverage_through_date__lt=OuterRef(
                                    "report__coverage_from_date"
                                ),
                            )
                            .values("committee_account_id")
                            .annotate(
                                incurred_prior=Sum("schedule_d__incurred_amount"),
                            )
                            .values("incurred_prior")
                        )
                    ),
                    Value(Decimal(0)),
                ),
            ),
            default=None,
        )

    def PAYMENT_PRIOR_CLAUSE(self):
        return Case(
            When(
                schedule_d__isnull=False,
                then=Coalesce(
                    Subquery(
                        super()
                        .get_queryset()
                        .annotate(date=self.DATE_CLAUSE, amount=self.AMOUNT_CLAUSE)
                        .filter(
                            ~Q(debt_id=OuterRef("id")),
                            debt__transaction_id=OuterRef("transaction_id"),
                            schedule_d__isnull=True,
                            date__lt=OuterRef("report__coverage_from_date"),
                        )
                        .values("committee_account_id")
                        .annotate(debt_payments_prior=Sum("amount"))
                        .values("debt_payments_prior")
                    ),
                    Value(Decimal(0)),
                ),
            ),
            default=None,
        )

    def PAYMENT_AMOUNT_CLAUSE(self):
        return Case(
            When(
                schedule_d__isnull=False,
                then=Coalesce(
                    Subquery(
                        super()
                        .get_queryset()
                        .filter(debt_id=OuterRef("id"), schedule_d__isnull=True)
                        .annotate(amount=self.AMOUNT_CLAUSE)
                        .values("committee_account_id")
                        .annotate(payment_to_date=Sum("amount"))
                        .values("payment_to_date")
                    ),
                    Value(Decimal(0)),
                ),
            ),
            default=None,
        )

    def transaction_view(self):
        return (
            super()
            .get_queryset()
            .annotate(
                schedule=self.SCHEDULE_CLAUSE(),
                date=self.DATE_CLAUSE,
                amount=self.AMOUNT_CLAUSE,
                effective_amount=self.EFFECTIVE_AMOUNT_CLAUSE,
                aggregate=self.ENTITY_AGGREGGATE_CLAUSE(),
                back_reference_tran_id_number=self.BACK_REFERENCE_CLAUSE(),
                _calendar_ytd_per_election_office=self.ELECTION_AGGREGATE_CLAUSE(),
                incurred_prior=self.INCURRED_PRIOR_CLAUSE(),
                payment_prior=self.PAYMENT_PRIOR_CLAUSE(),
                payment_amount=self.PAYMENT_AMOUNT_CLAUSE(),
                loan_key=self.LOAN_KEY_CLAUSE(),
                loan_payment_to_date=self.LOAN_PAYMENT_CLAUSE(),
                # do after view: loan_balance=F("amount") - F("loan_payment_to_date"),
                # debt_key=Case(
                #     When(
                #         Q(debt_id__isnull=False)
                #         & Q(
                #             schedule__in=[
                #                 Schedule.A.value,
                #                 Schedule.B.value,
                #                 Schedule.E.value,
                #             ]
                #         ),
                #         then=Concat(F("debt__transaction_id"), F("date")),
                #     ),
                #     When(
                #         schedule_d__isnull=False,
                #         then=Concat(
                #             F("transaction_id"), F("report__coverage_from_date")
                #         ),
                #     ),
                #     default=None,
                #     output_field=TextField(),
                # ),
                # debt_payment=Case(
                #     When(
                #         schedule_d__isnull=False,
                #         then=Window(
                #             expression=Sum("effective_amount"),
                #             **self.debt_payment_window
                #         )
                #         - F("effective_amount"),
                #     ),
                #     default=Value(0.0),
                #     output_field=DecimalField(),
                # ),
                # do after view
                # balance=Coalesce(
                #     F("loan_balance"),
                #     Value(
                #         Decimal(0.0)
                #     ),  # F("balance_at_close"), F("loan_balance"), Value(Decimal(0.0))
                # ),
                line_label_order_key=F("_form_type"),
                _itemized=self.ITEMIZATION_CLAUSE(),
                # children=ArraySubquery(
                #     super()
                #     .get_queryset()
                #     .filter(parent_transaction_id=OuterRef("id"))
                #     .values("id")
                # ),
                name=self.DISPLAY_NAME_CLAUSE,
                transaction_ptr_id=F("id"),
            )
            # .filter(committee_account_id=committee.id)
        )


class TransactionViewManager(Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                beginning_balance=Case(
                    When(
                        schedule_d__isnull=False,
                        then=F("incurred_prior") - F("payment_prior"),
                    ),
                ),
                balance_at_close=Case(
                    When(
                        schedule_d__isnull=False,
                        then=F("beginning_balance")
                        + F("schedule_d__incurred_amount")
                        - F("payment_amount"),
                    ),
                ),
                balance=When(
                    schedule_d__isnull=False,
                    then=Coalesce(F("balance_at_close"), Value(Decimal(0.0))),
                ),
                itemized=Coalesce(
                    "view_parent_transaction__view_parent_transaction___itemized",
                    "view_parent_transaction___itemized",
                    "_itemized",
                ),
                calendar_ytd_per_election_office=Coalesce(
                    "view_parent_transaction___calendar_ytd_per_election_office",
                    "_calendar_ytd_per_election_office",
                ),
            )
        )


class Schedule(Enum):
    A = Value("A")
    B = Value("B")
    C = Value("C")
    C2 = Value("C1")
    C1 = Value("C2")
    D = Value("D")
    E = Value("E")
