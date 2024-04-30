from django.db import transaction as db_transaction
from rest_framework import filters, pagination

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from datetime import datetime
from django.db.models import Q
from fecfiler.committee_accounts.views import CommitteeOwnedViewMixin
from fecfiler.transactions.models import (
    Transaction,
    SCHEDULE_TO_TABLE,
    Schedule,
    get_read_model,
)
from fecfiler.transactions.serializers import (
    TransactionSerializer,
    SCHEDULE_SERIALIZERS,
)
from fecfiler.reports.models import Report, update_recalculation
from fecfiler.contacts.models import Contact
from fecfiler.contacts.serializers import create_or_update_contact
from fecfiler.transactions.schedule_c.views import save_hook as schedule_c_save_hook
from fecfiler.transactions.schedule_c2.views import save_hook as schedule_c2_save_hook
from fecfiler.transactions.schedule_d.views import save_hook as schedule_d_save_hook
import structlog

import os
import psycopg2

logger = structlog.get_logger(__name__)


class TransactionListPagination(pagination.PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"


class TransactionViewSet(CommitteeOwnedViewMixin, ModelViewSet):
    serializer_class = TransactionSerializer
    pagination_class = TransactionListPagination
    filter_backends = [filters.OrderingFilter]
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
    ]
    ordering = ["-created"]
    queryset = Transaction.objects

    def get_queryset(self):
        # Use the table if writing
        if hasattr(self, "action") and self.action in [
            "create",
            "update",
            "delete",
            "save_transactions",
        ]:
            queryset = super().get_queryset()
        else:  # Otherwise, use the view for reading
            committee_uuid = self.get_committee_uuid()
            model = get_read_model(committee_uuid)
            queryset = model.objects
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
            )
        return queryset

    def create(self, request, *args, **kwargs):
        with db_transaction.atomic():
            saved_transaction = self.save_transaction(request.data, request)
            print(f"transaction ID: {saved_transaction.id}")
        # transaction_view = self.get_queryset().get(id=saved_transaction.id)
        return Response(TransactionSerializer().to_representation(saved_transaction))

    def update(self, request, *args, **kwargs):
        with db_transaction.atomic():
            saved_transaction = self.save_transaction(request.data, request)
        return Response(TransactionSerializer().to_representation(saved_transaction))

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
        except Exception:
            message = "contact_1_id, date, and aggregate_group are required params"
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        return self.get_previous(transaction_id, date, aggregation_group, contact_1_id)

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
        except Exception:
            message = """date, aggregate_group, election_code, and candidate_office are required params.
            candidate_state is required for HOUSE and SENATE.
            candidate_district is required for HOUSE"""
            return Response(message, status=status.HTTP_400_BAD_REQUEST)

        return self.get_previous(
            id, date, aggregation_group, None, election_code, office, state, district
        )

    def get_previous(
        self,
        transaction_id,
        date,
        aggregation_group,
        contact_id=None,
        election_code=None,
        office=None,
        state=None,
        district=None,
    ):
        date = datetime.fromisoformat(date)
        query = self.get_queryset().filter(
            ~Q(id=transaction_id or None),
            Q(date__year=date.year),
            Q(date__lte=date),
            Q(aggregation_group=aggregation_group),
        )
        if contact_id:
            query = query.filter(Q(contact_1_id=contact_id))
        else:
            query = query.filter(
                Q(schedule_e__election_code=election_code),
                Q(contact_2__candidate_office=office),
                Q(contact_2__candidate_state=state),
                Q(contact_2__candidate_district=district),
            )
        query = query.order_by("-date", "-created")
        previous_transaction = query.first()

        if previous_transaction:
            serializer = self.get_serializer(previous_transaction)
            return Response(data=serializer.data)

        response = {"message": "No previous transaction found."}
        return Response(response, status=status.HTTP_404_NOT_FOUND)

    def save_transaction(self, transaction_data, request):
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

        is_existing = "id" in transaction_data
        if is_existing:
            transaction_instance = Transaction.objects.get(pk=transaction_data["id"])
            transaction_serializer = TransactionSerializer(
                transaction_instance,
                data=transaction_data,
                context={"request": request},
            )
            schedule_serializer = SCHEDULE_SERIALIZERS.get(schedule)(
                transaction_instance.get_schedule(), data=transaction_data
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
                transaction_data, contact_key, request.session["committee_uuid"]
            )
            for contact_key in ["contact_1", "contact_2", "contact_3"]
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
        for report_id in report_ids:
            report = Report.objects.get(id=report_id)
            if transaction_instance.schedule_c and report.coverage_through_date:
                schedule_instance.report_coverage_through_date = (
                    report.coverage_through_date
                )
                schedule_instance.save()
            if (transaction_instance.schedule_d) and report.coverage_from_date:
                schedule_instance.report_coverage_from_date = report.coverage_from_date
                schedule_instance.save()

            update_recalculation(report)
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
                child_transaction = self.get_queryset().get(id=child_transaction_data)
                child_transaction.parent_transaction_id = transaction_instance.id
                child_transaction.save()
            else:
                child_transaction_data["parent_transaction_id"] = transaction_instance.id
                child_transaction_data.pop("parent_transaction", None)
                if child_transaction_data.get("use_parent_contact", None):
                    child_transaction_data["contact_1_id"] = (
                        transaction_instance.contact_1_id
                    )
                    del child_transaction_data["contact_1"]

                self.save_transaction(child_transaction_data, request)

        return self.queryset.get(id=transaction_instance.id)

    @action(detail=False, methods=["put"], url_path=r"multisave")
    def save_transactions(self, request):
        with db_transaction.atomic():
            saved_data = [self.save_transaction(data, request) for data in request.data]
        return Response(
            [TransactionSerializer().to_representation(data) for data in saved_data]
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

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
                child["reatt_redes"] = reatt_redes
                child["reatt_redes_id"] = reatt_redes.id
                request.data[1]["children"] = [child]
                to = self.save_transaction(request.data[1], request)
                saved_data = [reatt_redes, to]
        return Response(
            [TransactionSerializer().to_representation(data) for data in saved_data]
        )

    @action(detail=False, methods=["post"], url_path=r"add-to-report")
    def add_transaction_to_report(self, request):
        try:
            report = Report.objects.get(id=request.data.get("report_id"))
        except Report.DoesNotExist:
            return Response("No report matching id provided", status=404)

        try:
            transaction = Transaction.objects.get(id=request.data.get("transaction_id"))
        except Transaction.DoesNotExist:
            return Response("No transaction matching id provided", status=404)

        transaction.reports.add(report)
        update_recalculation(report)
        return Response("Transaction added to report")

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
        update_recalculation(report)
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
        print(
            """Environment variable DATABASE_URL not found.
            Please check your settings and try again"""
        )
        exit(1)
    print("Testing connection...")
    conn = psycopg2.connect(database_uri)
    sql, params = qs.query.sql_with_params()
    with conn.cursor() as cursor:
        s = cursor.mogrify(sql, params)
    conn.close()
    return s
