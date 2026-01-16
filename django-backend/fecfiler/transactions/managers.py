from fecfiler.soft_delete.managers import SoftDeleteManager
from fecfiler.transactions.schedule_a.managers import (
    line_labels as line_labels_a,
)
from fecfiler.transactions.schedule_b.managers import (
    line_labels as line_labels_b,
)
from fecfiler.transactions.schedule_c.managers import line_labels as line_labels_c
from fecfiler.transactions.schedule_d.managers import line_labels as line_labels_d
from fecfiler.transactions.schedule_e.managers import line_labels as line_labels_e
from fecfiler.transactions.schedule_f.managers import line_labels as line_labels_f
from django.db.models.functions import Coalesce, Concat
from django.db.models import (
    Q,
    UUIDField,
    DecimalField,
    DateField,
    OuterRef,
    Subquery,
    F,
    Case,
    When,
    Value,
    TextField,
)
from decimal import Decimal
from enum import Enum
from ..reports.models import Report
from fecfiler.reports.report_code_label import report_code_label_case, report_type_case

"""Manager to deterimine fields that are used the same way across transactions,
but are called different names"""


class TransactionManager(SoftDeleteManager):

    def get_queryset(self):
        return super().get_queryset().annotate(date=self.DATE_CLAUSE)

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

    DATE_MAPPING = {
        "A": ["schedule_a__contribution_date"],
        "B": ["schedule_b__expenditure_date"],
        "C": ["schedule_c__loan_incurred_date"],
        "C1": [],
        "C2": [],
        "D": [],
        "E": ["schedule_e__disbursement_date", "schedule_e__dissemination_date"],
        "F": ["schedule_f__expenditure_date"],
    }

    AMOUNT_MAPPING = {
        "A": ["schedule_a__contribution_amount"],
        "B": ["schedule_b__expenditure_amount"],
        "C": ["schedule_c__loan_amount"],
        "C1": [],
        "C2": ["schedule_c2__guaranteed_amount"],
        "D": ["schedule_d__incurred_amount", "debt__schedule_d__incurred_amount"],
        "E": ["schedule_e__expenditure_amount"],
        "F": ["schedule_f__expenditure_amount"],
    }

    def transaction_list_view(self, schedules_to_include=None):
        if not schedules_to_include:
            active_schedules = self.DATE_MAPPING.keys()
        else:
            active_schedules = schedules_to_include

        # Schedules filtering
        schedule_cases = []
        SCHEDULE_ENUM_MAP = {
            "A": Schedule.A.value,
            "B": Schedule.B.value,
            "C": Schedule.C.value,
            "C1": Schedule.C1.value,
            "C2": Schedule.C2.value,
            "D": Schedule.D.value,
            "E": Schedule.E.value,
            "F": Schedule.F.value,
        }
        SCHEDULE_FIELD_MAP = {
            "A": "schedule_a__isnull",
            "B": "schedule_b__isnull",
            "C": "schedule_c__isnull",
            "C1": "schedule_c1__isnull",
            "C2": "schedule_c2__isnull",
            "D": "schedule_d__isnull",
            "E": "schedule_e__isnull",
            "F": "schedule_f__isnull",
        }

        for sched_id in active_schedules:
            field_check = SCHEDULE_FIELD_MAP.get(sched_id)
            enum_value = SCHEDULE_ENUM_MAP.get(sched_id)

            if field_check and enum_value:
                schedule_cases.append(When(Q(**{field_check: False}), then=enum_value))

        if schedule_cases:
            dynamic_schedule_clause = Case(*schedule_cases, output_field=TextField())
        else:
            dynamic_schedule_clause = Value(None, output_field=TextField())

        # Balance filtering
        is_c_active = "C" in active_schedules
        is_d_active = "D" in active_schedules
        if is_c_active:
            loan_balance_expr = F("amount") - Coalesce(
                F("loan_payment_to_date"), Value(Decimal("0.0"))
            )
        else:
            loan_balance_expr = Value(None, output_field=DecimalField())

        balance_cases = []

        if is_d_active:
            balance_cases.append(
                When(
                    schedule_d_id__isnull=False,
                    then=Coalesce(
                        F("schedule_d__balance_at_close"), Value(Decimal("0.0"))
                    ),
                )
            )

        if is_c_active:
            balance_cases.append(
                When(
                    schedule_c_id__isnull=False,
                    then=Coalesce(F("loan_balance"), Value(Decimal("0.0"))),
                )
            )

        if balance_cases:
            balance_expr = Case(*balance_cases, output_field=DecimalField())
        else:
            balance_expr = Value(None, output_field=DecimalField())

        date_args = []
        amount_args = []

        for sched in active_schedules:
            date_fields = self.DATE_MAPPING.get(sched, [])
            amount_fields = self.AMOUNT_MAPPING.get(sched, [])

            for field in date_fields:
                date_args.append(F(field))

            for field in amount_fields:
                amount_args.append(F(field))

        while len(date_args) < 2:
            date_args.append(Value(None, output_field=DateField()))

        while len(amount_args) < 2:
            amount_args.append(Value(None, output_field=DecimalField()))

        dynamic_date_clause = Coalesce(*date_args, output_field=DateField())
        dynamic_amount_clause = Coalesce(*amount_args, output_field=DecimalField())

        return (
            super()
            .get_queryset()
            .prefetch_related("reports")
            .annotate(
                schedule=dynamic_schedule_clause,
                date=dynamic_date_clause,
                amount=dynamic_amount_clause,
                loan_balance=loan_balance_expr,
                balance=balance_expr,
                form_type=self.FORM_TYPE_CLAUSE,
                name=self.DISPLAY_NAME_CLAUSE,
                transaction_ptr_id=F("id"),
                line_label=self.LINE_LABEL_CLAUSE(),
                report_code_label=self.REPORT_CODE_LABEL_CLAUSE(),
                loan_agreement_id=self.LOAN_AGREEMENT_CLAUSE(),
                report_type=self.REPORT_TYPE_CLAUSE(),
            )
            .alias(order_key=self.ORDER_KEY_CLAUSE())
            .order_by("order_key")
        )

    def transaction_view(self):
        return (
            super()
            .get_queryset()
            .prefetch_related("reports")
            .annotate(
                schedule=self.SCHEDULE_CLAUSE(),
                date=self.DATE_CLAUSE,
                amount=self.AMOUNT_CLAUSE,
                incurred_prior=F("schedule_d__incurred_prior"),
                payment_prior=F("schedule_d__payment_prior"),
                payment_amount=F("schedule_d__payment_amount"),
                beginning_balance=F("schedule_d__beginning_balance"),
                balance_at_close=F("schedule_d__balance_at_close"),
                form_type=self.FORM_TYPE_CLAUSE,
                name=self.DISPLAY_NAME_CLAUSE,
                transaction_ptr_id=F("id"),
                back_reference_tran_id_number=self.BACK_REFERENCE_CLAUSE,
                back_reference_sched_name=self.BACK_REFERENCE_NAME_CLAUSE,
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
                        then=Coalesce(
                            F("schedule_d__balance_at_close"), Value(Decimal(0.0))
                        ),
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
                report_code_label=self.REPORT_CODE_LABEL_CLAUSE(),
                loan_agreement_id=self.LOAN_AGREEMENT_CLAUSE(),
                report_type=self.REPORT_TYPE_CLAUSE(),
            )
            .alias(order_key=self.ORDER_KEY_CLAUSE())
            .order_by("order_key")
        )

    def LOAN_AGREEMENT_CLAUSE(self):
        return Subquery(
            self.model._base_manager.filter(
                parent_transaction_id=OuterRef("pk"),
                transaction_type_identifier="C1_LOAN_AGREEMENT",
                deleted__isnull=True,
            ).values("id")[:1],
            output_field=UUIDField(),
        )

    def REPORT_CODE_LABEL_CLAUSE(self):
        return Subquery(  # noqa: N806
            Report.objects.filter(transactions=OuterRef("pk"))
            .annotate(report_code_label=report_code_label_case)
            .values("report_code_label")[:1]
        )

    def REPORT_TYPE_CLAUSE(self):
        return Subquery(  # noqa: N806
            Report.objects.filter(transactions=OuterRef("pk"))
            .annotate(report_type=report_type_case)
            .values("report_type")[:1]
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
    C1 = Value("C1")
    C2 = Value("C2")
    D = Value("D")
    E = Value("E")
    F = Value("F")
