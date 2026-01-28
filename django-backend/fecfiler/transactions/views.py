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
    TransactionListSerializer,
    SCHEDULE_SERIALIZERS,
)
from fecfiler.transactions.utils_aggregation_queries import (
    filter_queryset_for_previous_transactions_in_aggregation,
)
from fecfiler.transactions.utils_aggregation_prep import (
    create_old_snapshot,
    calculate_effective_amount,
)
from fecfiler.reports.models import Report
from fecfiler.contacts.models import Contact
from fecfiler.contacts.serializers import create_or_update_contact
from fecfiler.transactions.schedule_c.views import save_hook as schedule_c_save_hook
from fecfiler.transactions.schedule_c2.views import save_hook as schedule_c2_save_hook
from fecfiler.transactions.schedule_d.views import save_hook as schedule_d_save_hook
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

    def get_serializer_class(self):
        if self.action == "list":
            return TransactionListSerializer
        return TransactionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
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

        return queryset.prefetch_related("reports")

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
        return response

    def partial_update(self, request, pk=None):
        response = {"message": "Update function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return response

    @action(detail=True, methods=["put"], url_path="update-itemization-aggregation")
    def update_itemization_aggregation(self, request, pk=None):

        transaction: Transaction = self.get_object()
        transaction_data = self.get_serializer(transaction).data
        transaction_data["report_ids"] = [
            str(rep_id) for rep_id in transaction.reports.values_list("id", flat=True)
        ]

        allowed_fields = [
            "force_itemized",
            "force_unaggregated",
            "schedule_id",
            "schema_name",
        ]
        for field in allowed_fields:
            if field in request.data:
                transaction_data[field] = request.data[field]

        with db_transaction.atomic():
            self.save_transaction(transaction_data, request)

        return Response(transaction.id)

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

        # Track original instance for aggregation
        original_instance = None

        is_existing = "id" in transaction_data
        old_snapshot = None  # Initialize early

        if is_existing:
            original_instance = Transaction.objects.get(pk=transaction_data["id"])
            if original_instance is not None:
                # Capture old_snapshot IMMEDIATELY after loading, before serializer
                # modifies it
                if schedule in ["A", "B", "F"]:
                    eff = calculate_effective_amount(original_instance)
                    old_snapshot = create_old_snapshot(original_instance, eff)

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

        # Store old_snapshot on transaction instance so model.save() can access it
        if old_snapshot and original_instance:
            original_instance._passed_old_snapshot = old_snapshot

        # Pass old_snapshot to transaction.save() via kwargs (for schedules A, B, F)
        save_kwargs = {
            SCHEDULE_TO_TABLE[Schedule.__dict__[schedule]]: schedule_instance,
            **contact_instances,
        }

        transaction_instance = transaction_serializer.save(**save_kwargs)

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

        for child_transaction_data in children:
            if type(child_transaction_data) is str:
                # Capture old state BEFORE updating
                try:
                    child_instance = Transaction.objects.select_related(
                        "schedule_a", "schedule_b", "schedule_e", "contact_2"
                    ).get(id=child_transaction_data)

                    # Capture old snapshot if this is an aggregating schedule
                    old_snapshot = None
                    if child_instance.get_schedule_name() in [
                        Schedule.A,
                        Schedule.B,
                        Schedule.E,
                    ]:
                        eff = calculate_effective_amount(child_instance)
                        old_snapshot = create_old_snapshot(child_instance, eff)

                    # Update parent via model save to trigger aggregation
                    child_instance.parent_transaction_id = transaction_instance.id
                    if old_snapshot:
                        child_instance._passed_old_snapshot = old_snapshot
                    child_instance.save()
                except Transaction.DoesNotExist:
                    pass
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
        current_loan = Transaction.objects.get(pk=transaction.loan_id)
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
        current_debt = Transaction.objects.get(pk=transaction.debt_id)
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
