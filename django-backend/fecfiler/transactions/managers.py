from fecfiler.soft_delete.managers import SoftDeleteManager
from fecfiler.transactions.schedule_a.managers import (
    line_labels as line_labels_a,
    over_two_hundred_types as schedule_a_over_two_hundred_types,
)
from fecfiler.transactions.schedule_b.managers import (
    line_labels as line_labels_b,
    over_two_hundred_types as schedule_b_over_two_hundred_types,
    refunds as schedule_b_refunds,
)
from fecfiler.transactions.schedule_c.managers import line_labels as line_labels_c
from fecfiler.transactions.schedule_d.managers import line_labels as line_labels_d
from fecfiler.transactions.schedule_e.managers import line_labels as line_labels_e
from fecfiler.transactions.schedule_f.managers import line_labels as line_labels_f
from .constants import SCHEDULE_E_OVER_200_TYPES as schedule_e_over_two_hundred_types
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
    DecimalField,
    RowRange,
    Window,
    TextField,
)
from decimal import Decimal
from enum import Enum
from ..reports.models import Report
from fecfiler.reports.report_code_label import report_code_label_case
from .constants import ITEMIZATION_THRESHOLD
import structlog

logger = structlog.get_logger(__name__)

"""Manager to deterimine fields that are used the same way across transactions,
but are called different names"""


class TransactionManager(SoftDeleteManager):
    # Window definitions for aggregate calculations
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

    def get_queryset(self):
        return super().get_queryset().annotate(date=self.DATE_CLAUSE)

    def create(self, **kwargs):
        """Override create to aggregate schedules A/B/E, run itemization for all."""
        instance = super().create(**kwargs)

        # After direct INSERT, refresh and invoke service
        instance.refresh_from_db()

        try:
            schedule = instance.get_schedule_name()
            # Only schedules A, B, and E get aggregated
            if schedule in [Schedule.A, Schedule.B, Schedule.E]:
                try:
                    from .utils_aggregation import (
                        update_aggregates_for_affected_transactions,
                    )
                    update_aggregates_for_affected_transactions(instance, "create")
                except Exception:
                    logger.error(
                        "Failed to update aggregates via service on create",
                        transaction_id=instance.id,
                    )
            else:
                # For non-aggregating schedules, still update itemization
                try:
                    from .itemization import update_itemization
                    update_itemization(instance)
                    instance.save(update_fields=["itemized"])
                except Exception:
                    logger.error(
                        "Failed to update itemization on create",
                        transaction_id=instance.id,
                    )
        except Exception:
            # If get_schedule_name() fails, just return the instance
            pass
        return instance

    def SCHEDULE_CLAUSE(self):  # noqa: N802
        return Case(
            When(schedule_a__isnull=False, then=Schedule.A.value),
            When(schedule_b__isnull=False, then=Schedule.B.value),
            When(schedule_c__isnull=False, then=Schedule.C.value),
            When(schedule_c1__isnull=False, then=Schedule.C1.value),
            When(schedule_c2__isnull=False, then=Schedule.C2.value),
            When(schedule_d__isnull=False, then=Schedule.D.value),
            When(schedule_e__isnull=False, then=Schedule.E.value),
            When(schedule_f__isnull=False, then=Schedule.F.value),
        )

    DATE_CLAUSE = Coalesce(
        "schedule_a__contribution_date",
        "schedule_b__expenditure_date",
        "schedule_c__loan_incurred_date",
        "schedule_e__disbursement_date",
        "schedule_e__dissemination_date",
        "schedule_f__expenditure_date",
    )

    EFFECTIVE_AMOUNT_CLAUSE = Case(
        When(
            transaction_type_identifier__in=schedule_b_refunds,
            then=F("amount") * Value(Decimal(-1)),
        ),
        When(schedule_c__isnull=False, then=None),
        default="amount",
        output_field=DecimalField(),
    )

    AMOUNT_CLAUSE = Coalesce(
        "schedule_a__contribution_amount",
        "schedule_b__expenditure_amount",
        "schedule_c__loan_amount",
        "schedule_c2__guaranteed_amount",
        "schedule_e__expenditure_amount",
        "schedule_f__expenditure_amount",
        "debt__schedule_d__incurred_amount",
        "schedule_d__incurred_amount",
    )

    AGGREGATE = Case(
        When(force_unaggregated=True, then=Decimal(0)), default=F("effective_amount")
    )

    def ITEMIZATION_CLAUSE(self):  # noqa: N802
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
                aggregate__gt=Value(ITEMIZATION_THRESHOLD),
                then=Value(True),
            ),
            When(
                transaction_type_identifier__in=over_two_hundred_types,
                then=Value(False),
            ),
            default=Value(True),
            output_field=BooleanField(),
        )

    def ENTITY_AGGREGATE_CLAUSE(self):  # noqa: N802
        return Window(expression=Sum(self.AGGREGATE), **self.entity_aggregate_window)

    def ELECTION_AGGREGATE_CLAUSE(self):  # noqa: N802
        return Window(expression=Sum(self.AGGREGATE), **self.election_aggregate_window)

    BACK_REFERENCE_CLAUSE = Coalesce(
        F("reatt_redes__transaction_id"),
        F("parent_transaction__transaction_id"),
        F("debt__transaction_id"),
        F("loan__transaction_id"),
        Value(None),
    )

    BACK_REFERENCE_NAME_CLAUSE = Coalesce(
        F("reatt_redes___form_type"),
        F("parent_transaction___form_type"),
        F("debt___form_type"),
        F("loan___form_type"),
        Value(None),
    )

    # clause used to facilitate sorting on name as it's displayed
    DISPLAY_NAME_CLAUSE = Coalesce(
        "contact_1__name",
        Concat(
            "contact_1__last_name",
            Value(", "),
            "contact_1__first_name",
            output_field=TextField(),
        ),
    )

    FORM_TYPE_CLAUSE = Case(
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
    )

    def INCURRED_PRIOR_CLAUSE(self):  # noqa: N802
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
                                schedule_d__report_coverage_from_date__lt=OuterRef(
                                    "schedule_d__report_coverage_from_date"
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

    def PAYMENT_PRIOR_CLAUSE(self):  # noqa: N802
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
                            date__lt=OuterRef("schedule_d__report_coverage_from_date"),
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

    def PAYMENT_AMOUNT_CLAUSE(self):  # noqa: N802
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
        REPORT_CODE_LABEL_CLAUSE = Subquery(  # noqa: N806
            Report.objects.filter(transactions=OuterRef("pk"))
            .annotate(report_code_label=report_code_label_case)
            .values("report_code_label")[:1]
        )

        return (
            super()
            .get_queryset()
            .annotate(
                schedule=self.SCHEDULE_CLAUSE(),
                date=self.DATE_CLAUSE,
                amount=self.AMOUNT_CLAUSE,
                incurred_prior=self.INCURRED_PRIOR_CLAUSE(),
                payment_prior=self.PAYMENT_PRIOR_CLAUSE(),
                payment_amount=self.PAYMENT_AMOUNT_CLAUSE(),
                form_type=self.FORM_TYPE_CLAUSE,
                name=self.DISPLAY_NAME_CLAUSE,
                transaction_ptr_id=F("id"),
                back_reference_tran_id_number=self.BACK_REFERENCE_CLAUSE,
                back_reference_sched_name=self.BACK_REFERENCE_NAME_CLAUSE,
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
                loan_balance=Case(
                    When(
                        schedule_c__isnull=False,
                        then=F("amount")
                        - Coalesce(F("loan_payment_to_date"), Decimal(0.0)),
                    ),
                ),
                balance=Case(
                    When(
                        schedule_d__isnull=False,
                        then=Coalesce(F("balance_at_close"), Value(Decimal(0.0))),
                    ),
                    When(
                        schedule_c__isnull=False,
                        then=Coalesce(F("loan_balance"), Decimal(0)),
                    ),
                ),
                calendar_ytd_per_election_office=Coalesce(
                    "parent_transaction__parent_transaction___calendar_ytd_per_election_office",  # noqa
                    "parent_transaction___calendar_ytd_per_election_office",
                    "_calendar_ytd_per_election_office",
                ),
                line_label=self.LINE_LABEL_CLAUSE(),
                report_code_label=REPORT_CODE_LABEL_CLAUSE,
            )
            .alias(order_key=self.ORDER_KEY_CLAUSE())
            .order_by("order_key")
        )

    def ORDER_KEY_CLAUSE(self):  # noqa: N802
        return Case(
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
            default=Concat("schedule", "_form_type", "created", output_field=TextField()),
            output_field=TextField(),
        )

    A_11 = ["SA11A", "SA11AI", "SA11AII", "SA11B", "SA11C"]
    A = ["SA12", "SA13", "SA14", "SA15", "SA16", "SA17"]
    B = [
        "SB21B",
        "SB22",
        "SB23",
        "SB26",
        "SB27",
        "SB28A",
        "SB28B",
        "SB28C",
        "SB29",
        "SB30B",
    ]
    C = ["SC/9", "SC/10"]
    D = ["SD9", "SD10"]
    E = ["SE"]
    F = ["SF"]

    def LINE_LABEL_CLAUSE(self):  # noqa: N802
        label_map = {
            **line_labels_a,
            **line_labels_b,
            **line_labels_c,
            **line_labels_d,
            **line_labels_e,
            **line_labels_f,
        }
        return Case(
            *[
                When(form_type=line, then=Value(label))
                for line, label in label_map.items()
            ]
        )


class Schedule(Enum):
    A = Value("A")
    B = Value("B")
    C = Value("C")
    C2 = Value("C1")
    C1 = Value("C2")
    D = Value("D")
    E = Value("E")
    F = Value("F")
