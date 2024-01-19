import logging
from silk.profiling.profiler import silk_profile
from django.db import transaction as db_transaction
from rest_framework import filters, pagination

from django.core.paginator import Paginator as DjangoPaginator
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.mixins import (
    CreateModelMixin,
    UpdateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.viewsets import GenericViewSet, ModelViewSet
from datetime import datetime
from django.db.models import Q, Value
from django.db.models.fields import TextField
from django.db.models.functions import Coalesce, Concat
from fecfiler.committee_accounts.views import CommitteeOwnedViewMixin
from fecfiler.reports.views import ReportViewMixin, filter_by_report
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
from fecfiler.contacts.models import Contact
from fecfiler.transactions.schedule_c.views import save_hook as schedule_c_save_hook
from fecfiler.transactions.schedule_c2.views import save_hook as schedule_c2_save_hook
from fecfiler.transactions.schedule_d.views import save_hook as schedule_d_save_hook

import os
import psycopg2

logger = logging.getLogger(__name__)


class TransactionListPagination(pagination.PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"


class TransactionViewSet(
    CommitteeOwnedViewMixin,
    ReportViewMixin,
    ModelViewSet,
):
    serializer_class = TransactionSerializer
    pagination_class = TransactionListPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "line_label_order_key",
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
        if self.action in ["create", "update", "delete", "save_transactions"]:
            return super().get_queryset()

        # Otherwise, use the view for reading
        committee = self.get_committee()
        model = get_read_model(committee)
        print("AHOY")
        print(model.objects.all())
        queryset = filter_by_report(model.objects.all(), self)

        schedule_filters = self.request.query_params.get("schedules")
        if schedule_filters is not None:
            schedules_to_include = schedule_filters.split(",")
            queryset = queryset.filter(
                schedule__in=[
                    Schedule[schedule].value for schedule in schedules_to_include
                ]
            )

        parent_id = self.request.query_params.get("parent")
        # if parent_id:
        #     queryset = queryset.filter(parent_transaction_id=parent_id)

        print(queryset.query)
        return queryset

    @silk_profile(name="CREATE TRANSACTION")
    def create(self, request, *args, **kwargs):
        with db_transaction.atomic():
            saved_transaction = self.save_transaction(request.data, request)
            transaction_view = self.get_queryset().get(id=saved_transaction.id)
        return Response(TransactionSerializer().to_representation(transaction_view))

    @silk_profile(name="UPDATE TRANSACTION")
    def update(self, request, *args, **kwargs):
        with db_transaction.atomic():
            saved_transaction = self.save_transaction(request.data, request)
        return Response(TransactionSerializer().to_representation(saved_transaction))

    def partial_update(self, request, pk=None):
        response = {"message": "Update function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def propagate_contacts(self, transaction):
        committee_id = self.get_committee().id
        contact_1 = Contact.objects.get(id=transaction.contact_1_id)
        propagate_contact(committee_id, transaction, contact_1)
        contact_2 = Contact.objects.filter(id=transaction.contact_2_id).first()
        if contact_2:
            propagate_contact(committee_id, transaction, contact_2)
        contact_3 = Contact.objects.filter(id=transaction.contact_3_id).first()
        if contact_3:
            propagate_contact(committee_id, transaction, contact_3)

    def save_transaction(self, transaction_data, request):
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

        transaction_serializer.is_valid(raise_exception=True)
        schedule_serializer.is_valid(raise_exception=True)

        schedule_instance = schedule_serializer.save()
        transaction_instance = transaction_serializer.save(
            **{SCHEDULE_TO_TABLE[Schedule.__dict__[schedule]]: schedule_instance}
        )
        self.propagate_contacts(transaction_instance)

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
                child_transaction_data[
                    "parent_transaction_id"
                ] = transaction_instance.id
                child_transaction_data.pop("parent_transaction", None)
                if child_transaction_data.get("use_parent_contact", None):
                    child_transaction_data[
                        "contact_1_id"
                    ] = transaction_instance.contact_1_id
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

    @silk_profile(name="LIST TRANSACTIONS")
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
        response = super().list(request, *args, **kwargs)
        return response

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

    # I'd like to refactor this with keywords
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
                Q(schedule_e__so_candidate_office=office),
                Q(schedule_e__so_candidate_state=state),
                Q(schedule_e__so_candidate_district=district),
            )
        query = query.order_by("-date", "-created")
        previous_transaction = query.first()

        if previous_transaction:
            serializer = self.get_serializer(previous_transaction)
            return Response(data=serializer.data)

        response = {"message": "No previous transaction found."}
        return Response(response, status=status.HTTP_404_NOT_FOUND)


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


def propagate_contact(committee_id, transaction, contact):
    other_transactions = Transaction.objects.filter(
        ~Q(id=getattr(transaction, "id", None)),
        Q(Q(contact_1=contact) | Q(contact_2=contact) | Q(contact_3=contact)),
    )
    for other_transaction in other_transactions:
        other_transaction.get_schedule().update_with_contact(contact)
        other_transaction.save()


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
