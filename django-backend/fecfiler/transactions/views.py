from rest_framework import pagination
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from django.db.models import Q
from fecfiler.transactions.transaction_dependencies import (
    update_dependent_parent,
)
from fecfiler.committee_accounts.views import CommitteeOwnedViewMixin
from fecfiler.transactions.models import (
    Transaction,
    Schedule,
)
from fecfiler.transactions.serializers import TransactionSerializer
from fecfiler.reports.models import Report
from fecfiler.contacts.models import Contact
from .services import TransactionService
import structlog
import psycopg2
import os

logger = structlog.get_logger(__name__)


class TransactionListPagination(pagination.PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"


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
                or (
                    type(self.request.data) is not list
                    and self.request.data.get("report_id")
                )
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
        saved_transaction = TransactionService().save_transaction(
            request.data, request, self.get_queryset(), True
        )
        logger.info(f"Created new transaction: {saved_transaction.id}")
        return Response(saved_transaction.id)

    def update(self, request, *args, **kwargs):
        saved_transaction = TransactionService().save_transaction(
            request.data, request, self.get_queryset()
        )
        return Response(saved_transaction.id)

    def destroy(self, request, *args, **kwargs):
        # capture copy of transaction before deletion to use in update_dependent_parent
        transaction = self.get_object()
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

        previous_transaction = TransactionService().get_previous(
            self.get_queryset(), date, aggregation_group, transaction_id, contact_1_id
        )
        if previous_transaction:
            serializer = self.get_serializer(previous_transaction)
            return Response(data=serializer.data)
        else:
            response = {"message": "No previous transaction found."}
            return Response(response, status=status.HTTP_404_NOT_FOUND)

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

        previous_transaction = TransactionService().get_previous(
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
        if previous_transaction:
            serializer = self.get_serializer(previous_transaction)
            return Response(data=serializer.data)
        else:
            response = {"message": "No previous transaction found."}
            return Response(response, status=status.HTTP_404_NOT_FOUND)

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

        previous_transaction = TransactionService().get_previous(
            self.get_queryset(),
            date,
            aggregation_group,
            transaction_id,
            None,
            contact_2_id,
            None,
            general_election_year,
        )
        if previous_transaction:
            serializer = self.get_serializer(previous_transaction)
            return Response(data=serializer.data)
        else:
            response = {"message": "No previous transaction found."}
            return Response(response, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["put"], url_path=r"multisave/reattribution")
    def save_reatt_redes_transactions(self, request):
        if request.data[0].get("id", None) is not None:
            saved_data = [
                TransactionService().save_transaction(data, request, self.get_queryset())
                for data in request.data
            ]
        else:
            reatt_redes = TransactionService().save_transaction(
                request.data[0], request, self.get_queryset()
            )
            request.data[1]["reatt_redes"] = reatt_redes
            request.data[1]["reatt_redes_id"] = reatt_redes.id
            child = request.data[1].get("children", [])[0]
            child[" "] = reatt_redes
            child["reatt_redes_id"] = reatt_redes.id
            request.data[1]["children"] = [child]
            to = TransactionService().save_transaction(
                request.data[1], request, self.get_queryset()
            )
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


def stringify_queryset(qs):
    database_uri = os.environ.get("DATABASE_URL")
    if not database_uri:
        logger.error(
            """Environment variable DATABASE_URL not found.
            Please check your settings and try again"""
        )
        exit(1)
    logger.info("Testing connection...")
    conn = psycopg2.connect(database_uri)
    sql, params = qs.query.sql_with_params()
    with conn.cursor() as cursor:
        s = cursor.mogrify(sql, params)
    conn.close()
    return s
