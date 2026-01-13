from django.db import transaction as db_transaction, models
from rest_framework import pagination
from rest_framework.filters import OrderingFilter

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from datetime import datetime
from django.db.models import Q
from fecfiler.transactions.transaction_dependencies import (
    update_dependent_children,
    update_dependent_parent,
)
from fecfiler.committee_accounts.views import CommitteeOwnedViewMixin
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
)  # noqa: E501
from fecfiler.reports.models import Report
from fecfiler.contacts.models import Contact
from fecfiler.contacts.serializers import create_or_update_contact
from fecfiler.transactions.schedule_c.views import save_hook as schedule_c_save_hook
from fecfiler.transactions.schedule_c2.views import save_hook as schedule_c2_save_hook
from fecfiler.transactions.schedule_d.views import save_hook as schedule_d_save_hook
from fecfiler.transactions.aggregation import (
    process_aggregation_for_debts,
    process_aggregation_by_payee_candidate,
)
import structlog

import os
import psycopg

logger = structlog.get_logger(__name__)


class TransactionListPagination(pagination.PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"
    max_page_size = 20


class TransactionOrderingFilter(OrderingFilter):
    def get_ordering(self, request, queryset, view):
        ordering_query_param = request.query_params.get(self.ordering_param)
        ordering_fields = getattr(view, "ordering_fields", [])

        if ordering_query_param:
            fields = [param.strip() for param in ordering_query_param.split(",")]
            ordering = []
            for field in fields:
                if field.strip("-") in ordering_fields:
                    if field == "-memo_code" and not (
                        queryset.filter(memo_code=True).exists()
                        and queryset.exclude(memo_code=True).exists()
                    ):
                        field = "memo_code"
                    ordering.append(field)
            if ordering:
                return ordering

        return self.get_default_ordering(view)

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if ordering:
            return queryset.order_by(*ordering)
        return queryset


class TransactionViewSet(CommitteeOwnedViewMixin, ModelViewSet):
    serializer_class = TransactionSerializer
    pagination_class = TransactionListPagination
    filter_backends = [TransactionOrderingFilter]
    ordering_fields = [
        "line_label",
        "created",
        "transaction_type_identifier",
        "memo_code",
        "name",
        "date",
        "amount",
        "aggregate",
        "balance",
        "back_reference_tran_id_number",
        "form_type",
        "report_code_label",
    ]
    ordering = ["-created"]
    queryset = Transaction.objects

    def get_queryset(self):
        # Use the table if writing
        if hasattr(self, "action") and self.action in [
            "create",
            "update",
            "destroy",
            "save_transactions",
        ]:
            queryset = super().get_queryset()
        else:  # Otherwise, use the view for reading
            committee_uuid = self.get_committee_uuid()
            queryset = Transaction.objects.transaction_view().filter(
                committee_account__id=committee_uuid
            )

        report_id = (
            (
                self.request.query_params.get("report_id")
                or self.request.data.get("report_id")
            )
            if self.request
            else None
        )
        queryset = queryset.filter(reports__id=report_id) if report_id else queryset

        schedule_filters = self.request.query_params.get("schedules")
        if schedule_filters is not None:
            schedules_to_include = schedule_filters.split(",") if schedule_filters else []
            queryset = queryset.filter(
                schedule__in=[
                    Schedule[schedule].value for schedule in schedules_to_include
                ]
            )

        parent_id = self.request.query_params.get("parent")
        if parent_id:
            queryset = queryset.filter(parent_transaction_id=parent_id)

        contact_id = self.request.query_params.get("contact")
        if contact_id:
            queryset = queryset.filter(
                Q(contact_1=contact_id)
                | Q(contact_2=contact_id)
                | Q(contact_3=contact_id)
                | Q(contact_4=contact_id)
                | Q(contact_5=contact_id)
            )

        return queryset

    def create(self, request, *args, **kwargs):
        with db_transaction.atomic():
            saved_transaction = self.save_transaction(request.data, request)
            logger.info(f"Created new transaction: {saved_transaction.id}")
            update_dependent_parent(saved_transaction)
        return Response(saved_transaction.id)

    def update(self, request, *args, **kwargs):
        with db_transaction.atomic():
            saved_transaction = self.save_transaction(request.data, request)
        return Response(saved_transaction.id)

    def destroy(self, request, *args, **kwargs):
        # capture copy of transaction before deletion to use in update_dependent_parent
        transaction = self.get_object()
        with db_transaction.atomic():
            response = super().destroy(request, *args, **kwargs)
            # update parents that depend on this transaction
            update_dependent_parent(transaction)
            if transaction.is_debt_repayment():
                process_aggregation_for_debts(transaction.debt)
            elif transaction.schedule_d is not None:
                process_aggregation_for_debts(transaction)
        return response

    def partial_update(self, request, pk=None):
        response = {"message": "Update function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return response

    @action(detail=False, methods=["get"], url_path=r"previous/entity")
    def previous_transaction_by_entity(self, request):
        """Retrieves transaction that comes before this transactions,
        while being in the same group for aggregation"""
        transaction_id = request.query_params.get("transaction_id", None)
        try:
            contact_1_id = request.query_params["contact_1_id"]
            date = request.query_params["date"]
            aggregation_group = request.query_params["aggregation_group"]
            assert (
                date and contact_1_id and aggregation_group
            )  # Raises error if any value is not truthy (i.e, "" or None)
        except Exception:
            message = "contact_1_id, date, and aggregate_group are required params"
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        return self.get_previous(
            self.get_queryset(), date, aggregation_group, transaction_id, contact_1_id
        )

    @action(detail=False, methods=["get"], url_path=r"previous/election")
    def previous_transaction_by_election(self, request):
        """Retrieves transaction that comes before this transactions,
        while being in the same group for aggregation and the same election"""
        id = request.query_params.get("transaction_id", None)
        try:
            date = request.query_params["date"]
            aggregation_group = request.query_params["aggregation_group"]
            election_code = request.query_params["election_code"]
            office = request.query_params["candidate_office"]
            state = request.query_params.get("candidate_state", None)
            if office != Contact.CandidateOffice.PRESIDENTIAL and not state:
                raise Exception()
            district = request.query_params.get("candidate_district", None)
            if office == Contact.CandidateOffice.HOUSE and not district:
                raise Exception()

            assert (
                date and aggregation_group and election_code
            )  # Raises error if any value is not truthy (i.e, "" or None)
        except Exception:
            message = """date, aggregate_group, election_code, and candidate_office \
            are required params.
            candidate_state is required for HOUSE and SENATE.
            candidate_district is required for HOUSE"""
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        return self.get_previous(
            self.get_queryset(),
            date,
            aggregation_group,
            id,
            None,
            None,
            election_code,
            None,
            office,
            state,
            district,
        )

    @action(detail=False, methods=["get"], url_path=r"previous/payee-candidate")
    def previous_transaction_by_payee_candidate(self, request):
        """Retrieves transaction that comes before this transactions,
        while being in the same group for aggregation"""
        transaction_id = request.query_params.get("transaction_id", None)
        try:
            contact_2_id = request.query_params["contact_2_id"]
            date = request.query_params["date"]
            aggregation_group = request.query_params["aggregation_group"]
            general_election_year = request.query_params["general_election_year"]

            assert (
                contact_2_id and date and aggregation_group and general_election_year
            )  # Raises error if any value is not truthy (i.e, "" or None)
        except Exception:
            message = (
                "contact_2_id, date, aggregation_group, and "
                "general_election_year are required params"
            )

            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        return self.get_previous(
            self.get_queryset(),
            date,
            aggregation_group,
            transaction_id,
            None,
            contact_2_id,
            None,
            general_election_year,
        )

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

        if previous_transaction:
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
            serializer = self.get_serializer(previous_transaction)
            return Response(data=serializer.data)

        response = {"message": "No previous transaction found."}
        return Response(response, status=status.HTTP_404_NOT_FOUND)

    def save_transaction(self, transaction_data, request):
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
                    schedule_instance.report_coverage_through_date = coverage_through_date
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
        self.process_aggregation(
            transaction_instance,
            {
                "instance": original_instance,
                "date": original_date,
                "contact_1": original_contact_1,
                "contact_2": original_contact_2,
                "election_code": original_election_code,
                "election_year": original_election_year,
            },
        )

        for child_transaction_data in children:
            if type(child_transaction_data) is str:
                Transaction.objects.filter(id=child_transaction_data).update(
                    parent_transaction_id=transaction_instance.id
                )
            else:
                child_transaction_data["parent_transaction_id"] = transaction_instance.id
                child_transaction_data.pop("parent_transaction", None)
                if child_transaction_data.get("use_parent_contact", None):
                    child_transaction_data["contact_1_id"] = (
                        transaction_instance.contact_1_id
                    )
                    del child_transaction_data["contact_1"]

                self.save_transaction(child_transaction_data, request)

        """ trigger updates to transactions with fields that depend on this one
        EXAMPLE: if this transaction is a JF transfer, update the descriptions of its
        children and grandchildren transactions with any changes to the committee name
        """
        update_dependent_children(transaction_instance)
        delete_carried_forward_loans_if_needed(transaction_instance, committee_id)
        delete_carried_forward_debts_if_needed(transaction_instance, committee_id)

        # Set the earlier date in order to detect when a transaction has moved forward
        if original_date and original_date < schedule_instance.get_date():
            next_transactions_by_entity = (
                Transaction.objects.get_queryset()
                .filter(
                    ~Q(id=original_instance.id),
                    Q(date__year=original_date.year),
                    Q(contact_1=original_contact_1),
                    Q(date__gt=original_date)
                    | Q(date=original_date, created__gt=original_instance.created),
                )
                .order_by("date")
            )

            # Default next_transactions_by_election the same queryset as entities
            next_transactions_by_election = next_transactions_by_entity[:0]

            if original_contact_2 is not None:
                # Capturing these in variables to cut down on line width
                original_district = original_contact_2.candidate_district
                original_office = original_contact_2.candidate_office
                original_state = original_contact_2.candidate_state

                next_transactions_by_election = (
                    self.get_queryset()
                    .filter(
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
                    )
                    .order_by("date")
                )

            next_entity = next_transactions_by_entity.first()
            next_election = next_transactions_by_election.first()

            if next_entity is not None:
                next_entity.save()
            if next_election is not None:
                next_election.save()

        return self.queryset.get(id=transaction_instance.id)

    @action(detail=False, methods=["put"], url_path=r"multisave/reattribution")
    def save_reatt_redes_transactions(self, request):
        with db_transaction.atomic():
            if request.data[0].get("id", None) is not None:
                saved_data = [
                    self.save_transaction(data, request) for data in request.data
                ]
            else:
                reatt_redes = self.save_transaction(request.data[0], request)
                request.data[1]["reatt_redes"] = reatt_redes
                request.data[1]["reatt_redes_id"] = reatt_redes.id
                child = request.data[1].get("children", [])[0]
                child[" "] = reatt_redes
                child["reatt_redes_id"] = reatt_redes.id
                request.data[1]["children"] = [child]
                to = self.save_transaction(request.data[1], request)
                saved_data = [reatt_redes, to]
        ids = []
        for data in saved_data:
            ids.append(data.id)
        return Response(ids)

    # Manually process aggregation for a given transaction,
    # and if updating an existing transaction, check for edge cases
    def process_aggregation(self, transaction_instance, original_values):
        leapfrogged = False
        if original_values["instance"] is not None:
            leapfrogged = self.handle_date_leapfrogging(
                transaction_instance, original_values
            )
            self.handle_broken_transaction_chain(transaction_instance, original_values)

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
                    # process_aggregation_by_entity()
                    pass
                case Schedule.E:
                    # process_aggregation_by_election()
                    pass
                case Schedule.F:
                    process_aggregation_by_payee_candidate(transaction_instance)

        if transaction_instance.debt or transaction_instance.schedule_d is not None:
            process_aggregation_for_debts(transaction_instance)

    # If a transaction has been moved forward, update the aggregate values
    # for any transactions that were "leaped over"
    # Returns a boolean value based on whether or not a leapfrogging event occurred
    def handle_date_leapfrogging(self, transaction_instance, original_values):
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
                    self.handle_leapfrogging_election_year(original_values)
            return True
        return False

    def handle_leapfrogging_election_year(self, original_values):
        original_contact_2 = original_values["contact_2"]
        original_instance = original_values["instance"]
        original_election_year = original_values["election_year"]
        original_date = original_values["date"]

        # Handle date leap-frogging just for Schedule F transactions
        if original_contact_2 is not None and original_election_year:
            leapfrogged_sch_f_transactions = (
                self.get_queryset()
                .filter(
                    ~Q(id=original_instance.id),
                    Q(
                        contact_2_id=original_contact_2.id,
                        schedule_f__isnull=False,
                        schedule_f__general_election_year=original_election_year,
                    ),
                    Q(date__gt=original_date)
                    | Q(date=original_date, created__gt=original_instance.created),
                )
                .order_by("date")
            )

            to_recalculate = leapfrogged_sch_f_transactions.first()
            if to_recalculate is not None:
                process_aggregation_by_payee_candidate(to_recalculate)

    # If a transaction has been updated in such a way that would change which transactions
    # it would aggregate with, such as switching to a different contact or election code,
    # then recalculate the aggregates for the prior chain of transactions
    def handle_broken_transaction_chain(self, transaction_instance, original_values):
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
                # handle_broken_transaction_chain_entity
                pass
            case Schedule.E:
                # handle_broken_transaction_chain_election_code
                pass
            case Schedule.F:
                self.handle_broken_transaction_chain_election_year(
                    transaction_instance, original_values
                )

    def handle_broken_transaction_chain_election_year(
        self, transaction_instance, original_values
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
            leapfrogged_sch_f_transactions = (
                self.get_queryset()
                .filter(
                    ~Q(id=original_instance.id),
                    Q(
                        contact_2_id=original_contact_2.id,
                        schedule_f__isnull=False,
                        schedule_f__general_election_year=original_election_year,
                    ),
                    Q(date__gt=original_date)
                    | Q(date=original_date, created__gt=original_instance.created),
                )
                .order_by("date")
            )

            to_recalculate = leapfrogged_sch_f_transactions.first()
            if to_recalculate is not None:
                process_aggregation_by_payee_candidate(to_recalculate)

    @action(detail=False, methods=["post"], url_path=r"add-to-report")
    def add_transaction_to_report(self, request):
        try:
            report = Report.objects.get(id=request.data.get("report_id"))
        except Report.DoesNotExist:
            return Response("No report matching id provided", status=404)

        try:
            transaction = Transaction.objects.get(id=request.data.get("transaction_id"))
            transactions = transaction.get_transaction_family()
            for t in transactions:
                t.reports.add(report)
        except Transaction.DoesNotExist:
            return Response("No transaction matching id provided", status=404)

        return Response(f"Transaction(s) added to report: {[x.id for x in transactions]}")

    @action(detail=False, methods=["post"], url_path=r"remove-from-report")
    def remove_transaction_from_report(self, request):
        try:
            report = Report.objects.get(id=request.data.get("report_id"))
        except Report.DoesNotExist:
            return Response("No report matching id provided", status=404)

        try:
            transaction = Transaction.objects.get(id=request.data.get("transaction_id"))
        except Transaction.DoesNotExist:
            return Response("No transaction matching id provided", status=404)

        transaction.reports.remove(report)
        return Response("Transaction removed from report")


def noop(transaction, is_existing):
    pass


def get_save_hook(transaction: Transaction):
    schedule_name = transaction.get_schedule_name()
    hooks = {
        Schedule.C: schedule_c_save_hook,
        Schedule.C2: schedule_c2_save_hook,
        Schedule.D: schedule_d_save_hook,
    }
    return hooks.get(schedule_name, noop)


def stringify_queryset(qs):
    database_uri = os.environ.get("DATABASE_URL")
    if not database_uri:
        logger.error(
            """Environment variable DATABASE_URL not found.
            Please check your settings and try again"""
        )
        exit(1)
    logger.info("Testing connection...")
    conn = psycopg.connect(database_uri)
    sql, params = qs.query.sql_with_params()
    with conn.cursor() as cursor:
        s = cursor.mogrify(sql, params)
    conn.close()
    return s


def delete_carried_forward_loans_if_needed(transaction: Transaction, committee_id):
    if transaction.is_loan_repayment() is True:
        current_loan = Transaction.objects.transaction_view().get(pk=transaction.loan_id)
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
                    reports__id__in=models.Subquery(future_reports.values("id")),
                )
            )
            for transaction_to_delete in transactions_to_delete:
                transaction_to_delete.delete()


def delete_carried_forward_debts_if_needed(transaction: Transaction, committee_id):
    if transaction.is_debt_repayment() is True:
        current_debt = Transaction.objects.transaction_view().get(pk=transaction.debt_id)
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
                    reports__id__in=models.Subquery(future_reports.values("id")),
                )
            )
            for transaction_to_delete in transactions_to_delete:
                transaction_to_delete.delete()
        process_aggregation_for_debts(current_debt)
