from django.db import transaction as db_transaction
from datetime import datetime
from django.db.models import Q, Subquery
from fecfiler.transactions.transaction_dependencies import (
    update_dependent_children,
    update_dependent_parent,
)
from fecfiler.transactions.models import (
    Transaction,
    SCHEDULE_TO_TABLE,
    Schedule,
)
from fecfiler.transactions.serializers import (
    TransactionSerializer,
    SCHEDULE_SERIALIZERS,
)
from fecfiler.transactions.utils import (
    filter_queryset_for_previous_transactions_in_aggregation,
)
from fecfiler.reports.models import Report
from fecfiler.contacts.serializers import create_or_update_contact
from fecfiler.transactions.schedule_c.views import save_hook as schedule_c_save_hook
from fecfiler.transactions.schedule_c2.views import save_hook as schedule_c2_save_hook
from fecfiler.transactions.schedule_d.views import save_hook as schedule_d_save_hook
from fecfiler.transactions.schedule_f.models import ScheduleF
import structlog

logger = structlog.get_logger(__name__)


class TransactionService:
    def get_previous(
        self,
        queryset,
        date,
        aggregation_group,
        transaction_id=None,
        contact_1_id=None,
        contact_2_id=None,
        election_code=None,
        election_year=None,
        office=None,
        state=None,
        district=None,
    ):
        date = datetime.fromisoformat(date)
        previous_transactions = filter_queryset_for_previous_transactions_in_aggregation(
            queryset,
            date,
            aggregation_group,
            transaction_id,
            contact_1_id,
            contact_2_id,
            election_code,
            election_year,
            office,
            state,
            district,
        )
        previous_transaction = previous_transactions.first()

        original_transaction = None
        if transaction_id:
            original_transaction = queryset.get(id=transaction_id)

        if not previous_transaction:
            return None
        if original_transaction and (
            original_transaction.date < previous_transaction.date
            or (
                original_transaction.date == previous_transaction.date
                and original_transaction.created < previous_transaction.created
            )
        ):
            if previous_transaction.aggregate is not None:
                previous_transaction.aggregate -= original_transaction.amount
            if previous_transaction.calendar_ytd_per_election_office is not None:
                previous_transaction.calendar_ytd_per_election_office -= (
                    original_transaction.amount
                )
            if previous_transaction.schedule_f is not None:
                if (
                    original_transaction.schedule_f.general_election_year
                    == previous_transaction.schedule_f.general_election_year
                ):
                    previous_transaction.schedule_f.aggregate_general_elec_expended -= (  # noqa
                        original_transaction.amount
                    )

        return previous_transaction

    def save_transaction(self, transaction_data, request, queryset, update_parent=False):
        with db_transaction.atomic():
            committee_id = request.session["committee_uuid"]
            report_ids = transaction_data.pop("report_ids", [])
            children = transaction_data.pop("children", [])
            schedule = transaction_data.get("schedule_id")
            transaction_data["parent_transaction"] = transaction_data.get(
                "parent_transaction_id", None
            )
            transaction_data["debt"] = transaction_data.get("debt_id", None)
            transaction_data["loan"] = transaction_data.get("loan_id", None)
            transaction_data["reatt_redes"] = transaction_data.get("reatt_redes_id", None)
            if transaction_data.get("form_type"):
                transaction_data["_form_type"] = transaction_data["form_type"]

            # Original values used to manually trigger aggregate recalculation
            original_instance = None
            original_date = None
            original_contact_1 = None
            original_contact_2 = None
            original_election_code = None
            original_election_year = None

            is_existing = "id" in transaction_data
            if is_existing:
                original_instance = Transaction.objects.get(pk=transaction_data["id"])
                if original_instance is not None:
                    original_date = original_instance.get_date()
                    original_contact_1 = original_instance.contact_1
                    original_contact_2 = original_instance.contact_2
                    original_election_code = getattr(
                        original_instance.get_schedule(), "election_code", None
                    )
                    original_election_year = getattr(
                        original_instance.get_schedule(), "general_election_year", None
                    )

                transaction_serializer = TransactionSerializer(
                    original_instance,
                    data=transaction_data,
                    context={"request": request},
                )
                schedule_serializer = SCHEDULE_SERIALIZERS.get(schedule)(
                    original_instance.get_schedule(), data=transaction_data
                )
            else:
                transaction_serializer = TransactionSerializer(
                    data=transaction_data, context={"request": request}
                )
                schedule_serializer = SCHEDULE_SERIALIZERS.get(schedule)(
                    data=transaction_data, context={"request": request}
                )

            contact_instances = {
                contact_key: create_or_update_contact(
                    transaction_data, contact_key, committee_id
                )
                for contact_key in [
                    "contact_1",
                    "contact_2",
                    "contact_3",
                    "contact_4",
                    "contact_5",
                ]
                if contact_key in transaction_data
            }
            transaction_serializer.is_valid(raise_exception=True)
            schedule_serializer.is_valid(raise_exception=True)

            schedule_instance = schedule_serializer.save()
            transaction_instance = transaction_serializer.save(
                **{SCHEDULE_TO_TABLE[Schedule.__dict__[schedule]]: schedule_instance},
                **contact_instances,
            )

            # Link the transaction to all the reports it references in report_ids
            transaction_instance.reports.set(report_ids)
            if transaction_instance.schedule_c or transaction_instance.schedule_d:
                reports = Report.objects.filter(id__in=report_ids)
                coverage_through_date = None
                coverage_from_date = None

                for report in reports:
                    if transaction_instance.schedule_c and report.coverage_through_date:
                        coverage_through_date = report.coverage_through_date

                    if transaction_instance.schedule_d and report.coverage_from_date:
                        coverage_from_date = report.coverage_from_date

                if coverage_through_date or coverage_from_date:
                    if coverage_through_date:
                        schedule_instance.report_coverage_through_date = (
                            coverage_through_date
                        )
                    if coverage_from_date:
                        schedule_instance.report_coverage_from_date = coverage_from_date
                    schedule_instance.save()

            Report.objects.filter(committee_account_id=committee_id).update(
                calculation_status=None
            )
            logger.info(
                f"Transaction {transaction_instance.id} "
                f"linked to report(s): {', '.join(report_ids)}"
            )

            get_save_hook(transaction_instance)(
                transaction_instance,
                is_existing,
            )

            # Manually trigger aggregate recalculation
            # ---- Currently Schedule F only
            self._process_aggregation(
                transaction_instance,
                {
                    "instance": original_instance,
                    "date": original_date,
                    "contact_1": original_contact_1,
                    "contact_2": original_contact_2,
                    "election_code": original_election_code,
                    "election_year": original_election_year,
                },
                queryset,
            )

            for child_transaction_data in children:
                if type(child_transaction_data) is str:
                    Transaction.objects.filter(id=child_transaction_data).update(
                        parent_transaction_id=transaction_instance.id
                    )
                else:
                    child_transaction_data["parent_transaction_id"] = (
                        transaction_instance.id
                    )
                    child_transaction_data.pop("parent_transaction", None)
                    if child_transaction_data.get("use_parent_contact", None):
                        child_transaction_data["contact_1_id"] = (
                            transaction_instance.contact_1_id
                        )
                        del child_transaction_data["contact_1"]

                    self.save_transaction(child_transaction_data, request, queryset)

            """ trigger updates to transactions with fields that depend on this one
            EXAMPLE: if this transaction is a JF transfer, update the descriptions of its
            children and grandchildren transactions with any changes to the committee name
            """
            update_dependent_children(transaction_instance)
            self._delete_carried_forward_loans_if_needed(
                transaction_instance, committee_id
            )
            self._delete_carried_forward_debts_if_needed(
                transaction_instance, committee_id
            )

            # Set the earlier date in order to detect when a transaction has moved forward
            if original_date and original_date < schedule_instance.get_date():
                next_transactions_by_entity = queryset.filter(
                    ~Q(id=original_instance.id),
                    Q(date__year=original_date.year),
                    Q(contact_1=original_contact_1),
                    Q(date__gt=original_date)
                    | Q(date=original_date, created__gt=original_instance.created),
                ).order_by("date")

                # Default next_transactions_by_election the same queryset as entities
                next_transactions_by_election = next_transactions_by_entity[:0]

                if original_contact_2 is not None:
                    # Capturing these in variables to cut down on line width
                    original_district = original_contact_2.candidate_district
                    original_office = original_contact_2.candidate_office
                    original_state = original_contact_2.candidate_state

                    next_transactions_by_election = queryset.filter(
                        ~Q(id=original_instance.id),
                        Q(
                            contact_2__candidate_district=original_district,
                            contact_2__candidate_office=original_office,
                            contact_2__candidate_state=original_state,
                        ),
                        Q(date__gt=original_date)
                        | Q(date=original_date, created__gt=original_instance.created),
                        Q(
                            schedule_e__isnull=False,
                            schedule_e__election_code=original_election_code,
                        ),
                    ).order_by("date")

                next_entity = next_transactions_by_entity.first()
                next_election = next_transactions_by_election.first()

                if next_entity is not None:
                    next_entity.save()
                if next_election is not None:
                    next_election.save()

        transaction = Transaction.objects.get(id=transaction_instance.id)
        if update_parent:
            update_dependent_parent(transaction)

        return transaction

    def _process_aggregation_by_payee_candidate(self, transaction_instance, queryset):
        # Get the transaction out of the queryset in order to populate annotated fields
        transaction = queryset.filter(id=transaction_instance.id).first()
        if transaction is None or transaction.contact_2 is None:
            return

        shared_entity_transactions = queryset.filter(
            date__year=transaction.date.year,
            contact_2=transaction.contact_2,
            aggregation_group=transaction.aggregation_group,
            schedule_f__isnull=False,
            schedule_f__general_election_year=transaction.schedule_f.general_election_year,  # noqa: E501
        )

        previous_transactions = filter_queryset_for_previous_transactions_in_aggregation(
            shared_entity_transactions,
            transaction.date,
            transaction.aggregation_group,
            transaction.id,
            None,
            transaction.contact_2.id,
            None,
            transaction.schedule_f.general_election_year,
        )

        to_update = shared_entity_transactions.filter(
            Q(id=transaction.id)
            | Q(date__gt=transaction.date)
            | Q(Q(date=transaction.date) & Q(created__gt=transaction.created))
        ).order_by("date", "created")

        previous_transaction = previous_transactions.first()
        updated_schedule_fs = []
        for trans in to_update:
            previous_aggregate = 0
            if previous_transaction:
                previous_aggregate = (
                    previous_transaction.schedule_f.aggregate_general_elec_expended
                )

            trans.schedule_f.aggregate_general_elec_expended = (
                trans.schedule_f.expenditure_amount + previous_aggregate
            )
            updated_schedule_fs.append(trans.schedule_f)
            previous_transaction = trans

        ScheduleF.objects.bulk_update(
            updated_schedule_fs, ["aggregate_general_elec_expended"], batch_size=64
        )

    # Manually process aggregation for a given transaction,
    # and if updating an existing transaction, check for edge cases
    def _process_aggregation(self, transaction_instance, original_values, queryset):
        leapfrogged = False
        if original_values["instance"] is not None:
            leapfrogged = self._handle_date_leapfrogging(
                transaction_instance, original_values, queryset
            )
            self._handle_broken_transaction_chain(
                transaction_instance, original_values, queryset
            )

        if not leapfrogged:
            schedule = transaction_instance.get_schedule_name()
            match schedule:
                case (
                    Schedule.A
                    | Schedule.B
                    | Schedule.C
                    | Schedule.C1
                    | Schedule.C2
                    | Schedule.D
                ):  # noqa: E501
                    # _process_aggregation_by_entity()
                    pass
                case Schedule.E:
                    # _process_aggregation_by_election()
                    pass
                case Schedule.F:
                    self._process_aggregation_by_payee_candidate(
                        transaction_instance, queryset
                    )

    # If a transaction has been moved forward, update the aggregate values
    # for any transactions that were "leaped over"
    # Returns a boolean value based on whether or not a leapfrogging event occurred
    def _handle_date_leapfrogging(self, transaction_instance, original_values, queryset):
        schedule = transaction_instance.get_schedule()
        schedule_type = transaction_instance.get_schedule_name()
        original_date = original_values["date"]
        # Set the earlier date in order to detect when a transaction has moved forward
        if original_date and original_date < schedule.get_date():
            match schedule_type:
                case (
                    Schedule.A
                    | Schedule.B
                    | Schedule.C
                    | Schedule.C1
                    | Schedule.C2
                    | Schedule.D
                ):  # noqa: E501
                    # handle_leapfrogging_entity
                    pass
                case Schedule.E:
                    # handle_leapfrogging_election_code
                    pass
                case Schedule.F:
                    self._handle_leapfrogging_election_year(original_values, queryset)
            return True
        return False

    def _handle_leapfrogging_election_year(self, original_values, queryset):
        original_contact_2 = original_values["contact_2"]
        original_instance = original_values["instance"]
        original_election_year = original_values["election_year"]
        original_date = original_values["date"]

        # Handle date leap-frogging just for Schedule F transactions
        if original_contact_2 is not None and original_election_year:
            leapfrogged_sch_f_transactions = queryset.filter(
                ~Q(id=original_instance.id),
                Q(
                    contact_2_id=original_contact_2.id,
                    schedule_f__isnull=False,
                    schedule_f__general_election_year=original_election_year,
                ),
                Q(date__gt=original_date)
                | Q(date=original_date, created__gt=original_instance.created),
            ).order_by("date")

            to_recalculate = leapfrogged_sch_f_transactions.first()
            if to_recalculate is not None:
                self._process_aggregation_by_payee_candidate(to_recalculate, queryset)

    # If a transaction has been updated in such a way that would change which transactions
    # it would aggregate with, such as switching to a different contact or election code,
    # then recalculate the aggregates for the prior chain of transactions
    def _handle_broken_transaction_chain(
        self, transaction_instance, original_values, queryset
    ):
        schedule = transaction_instance.get_schedule_name()
        match schedule:
            case (
                Schedule.A
                | Schedule.B
                | Schedule.C
                | Schedule.C1
                | Schedule.C2
                | Schedule.D
            ):  # noqa: E501
                # _handle_broken_transaction_chain_entity
                pass
            case Schedule.E:
                # _handle_broken_transaction_chain_election_code
                pass
            case Schedule.F:
                self._handle_broken_transaction_chain_election_year(
                    transaction_instance, original_values, queryset
                )

    def _handle_broken_transaction_chain_election_year(
        self, transaction_instance, original_values, queryset
    ):
        original_election_year = original_values["election_year"]
        original_instance = original_values["instance"]
        original_contact_2 = original_values["contact_2"]
        original_date = original_values["date"]

        if (
            original_election_year is not None
            and original_election_year
            != transaction_instance.schedule_f.general_election_year  # noqa: E501
        ):
            leapfrogged_sch_f_transactions = queryset.filter(
                ~Q(id=original_instance.id),
                Q(
                    contact_2_id=original_contact_2.id,
                    schedule_f__isnull=False,
                    schedule_f__general_election_year=original_election_year,
                ),
                Q(date__gt=original_date)
                | Q(date=original_date, created__gt=original_instance.created),
            ).order_by("date")

            to_recalculate = leapfrogged_sch_f_transactions.first()
            if to_recalculate is not None:
                self._process_aggregation_by_payee_candidate(to_recalculate, queryset)

    def _delete_carried_forward_loans_if_needed(
        self, transaction: Transaction, committee_id
    ):
        if transaction.is_loan_repayment() is True:
            current_loan = Transaction.objects.transaction_view().get(
                pk=transaction.loan_id
            )
            current_loan_balance = current_loan.loan_balance
            original_loan_id = current_loan.loan_id or current_loan.id
            if current_loan_balance == 0:
                current_report = transaction.reports.filter(
                    Q(form_3x__isnull=False) | Q(form_3__isnull=False)
                ).first()
                future_reports = current_report.get_future_reports()
                transactions_to_delete = list(
                    Transaction.objects.filter(
                        loan_id=original_loan_id,
                        reports__id__in=Subquery(future_reports.values("id")),
                    )
                )
                for transaction_to_delete in transactions_to_delete:
                    transaction_to_delete.delete()

    def _delete_carried_forward_debts_if_needed(
        self, transaction: Transaction, committee_id
    ):
        if transaction.is_debt_repayment() is True:
            current_debt = Transaction.objects.transaction_view().get(
                pk=transaction.debt_id
            )
            current_debt_balance = current_debt.balance_at_close
            original_debt_id = current_debt.debt_id or current_debt.id
            if current_debt_balance == 0:
                current_report = transaction.reports.filter(
                    Q(form_3x__isnull=False) | Q(form_3__isnull=False)
                ).first()
                future_reports = current_report.get_future_reports()
                transactions_to_delete = list(
                    Transaction.objects.filter(
                        debt_id=original_debt_id,
                        reports__id__in=Subquery(future_reports.values("id")),
                    )
                )
                for transaction_to_delete in transactions_to_delete:
                    transaction_to_delete.delete()


def get_save_hook(transaction: Transaction):
    schedule_name = transaction.get_schedule_name()
    hooks = {
        Schedule.C: schedule_c_save_hook,
        Schedule.C2: schedule_c2_save_hook,
        Schedule.D: schedule_d_save_hook,
    }
    return hooks.get(schedule_name, noop)


def noop(transaction, is_existing):
    pass
