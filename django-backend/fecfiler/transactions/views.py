import logging
from django.db import transaction as db_transaction
from rest_framework import filters, pagination
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from django.db.models import Q, Value
from django.db.models.fields import TextField
from django.db.models.functions import Coalesce, Concat
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.reports.views import ReportViewMixin
from fecfiler.transactions.models import Transaction, SCHEDULE_TO_TABLE, Schedule
from fecfiler.transactions.serializers import (
    TransactionSerializerBase,
    TransactionSerializer,
    SCHEDULE_SERIALIZERS,
)
from fecfiler.contacts.serializers import ContactSerializer
from fecfiler.contacts.models import Contact
from fecfiler.transactions.schedule_a.serializers import ScheduleATransactionSerializer
from fecfiler.transactions.schedule_b.serializers import ScheduleBTransactionSerializer
from fecfiler.transactions.schedule_c.serializers import ScheduleCTransactionSerializer
from fecfiler.transactions.schedule_c1.serializers import (
    ScheduleC1TransactionSerializer,
)
from fecfiler.transactions.schedule_c2.serializers import (
    ScheduleC2TransactionSerializer,
)
from fecfiler.transactions.schedule_d.serializers import ScheduleDTransactionSerializer
from fecfiler.transactions.schedule_e.serializers import ScheduleETransactionSerializer


from rest_framework.exceptions import ErrorDetail, ValidationError

logger = logging.getLogger(__name__)


def save_transaction(request):
    """Handle the saving of a strictly parent/child pair.

    The child is removed from the parent and saved separately with the
    parent_transaction_id so that each schedule serializer can handle
    just its specific schedule fields and validation rules
    """
    transaction_data = request.data
    children_data = request.data["children"]
    transaction_data["children"] = []

    serializers = dict(
        A=ScheduleATransactionSerializer,
        B=ScheduleBTransactionSerializer,
        C=ScheduleCTransactionSerializer,
        C1=ScheduleC1TransactionSerializer,
        C2=ScheduleC2TransactionSerializer,
        D=ScheduleDTransactionSerializer,
        E=ScheduleETransactionSerializer,
    )

    schedule_serializer = serializers.get(transaction_data.get("schedule_id"))

    if "id" in transaction_data:
        transaction_obj = Transaction.objects.get(pk=transaction_data["id"])
        transaction_serializer = schedule_serializer(
            transaction_obj, data=transaction_data
        )
    else:
        transaction_serializer = schedule_serializer(data=transaction_data)

    with db_transaction.atomic():
        transaction_serializer.context["request"] = request
        if transaction_serializer.is_valid(raise_exception=True):
            transaction_obj = transaction_serializer.save()

            for child_transaction_data in children_data:
                child_transaction_data["parent_transaction_id"] = transaction_obj.id
                if child_transaction_data.pop("use_parent_contact", None):
                    child_transaction_data[
                        "contact_1_id"
                    ] = transaction_obj.contact_1_id
                    child_transaction_data[
                        "contact_1"
                    ] = ContactSerializer().to_representation(transaction_obj.contact_1)

                child_schedule_serializer = serializers.get(
                    child_transaction_data.get("schedule_id")
                )

                if "id" in child_transaction_data:
                    child_transaction_obj = Transaction.objects.get(
                        pk=child_transaction_data["id"]
                    )
                    child_transaction_serializer = child_schedule_serializer(
                        child_transaction_obj, data=child_transaction_data
                    )
                else:
                    child_transaction_serializer = child_schedule_serializer(
                        data=child_transaction_data
                    )

                child_transaction_serializer.context["request"] = request
                if child_transaction_serializer.is_valid(raise_exception=True):
                    child_transaction_serializer.save()

            # All parent and child transaction saves were successful, return
            # parent transaction
            return Response(schedule_serializer(transaction_obj).data)


def save_transaction3(transaction_data, request):
    children = transaction_data.pop("children", [])
    schedule = transaction_data.get("schedule_id")
    transaction_data["parent_transaction"] = transaction_data.get(
        "parent_transaction_id", None
    )

    if "id" in transaction_data:
        transaction_instance = Transaction.objects.get(pk=transaction_data["id"])
        transaction_serializer = TransactionSerializer(
            transaction_instance, data=transaction_data, context={"request": request}
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

    for child_transaction_data in children:
        child_transaction_data["parent_transaction_id"] = transaction_instance.id
        del child_transaction_data["parent_transaction"]
        if child_transaction_data.pop("use_parent_contact", None):
            child_transaction_data["contact_1_id"] = transaction_instance.contact_1_id

        save_transaction3(child_transaction_data, request)

    return transaction_instance


class TransactionListPagination(pagination.PageNumberPagination):
    page_size = 5
    page_size_query_param = "page_size"


class TransactionViewSet(CommitteeOwnedViewSet, ReportViewMixin):
    queryset = Transaction.objects.all().alias(
        name=Coalesce(
            Coalesce(
                "schedule_a__contributor_organization_name",
                "schedule_b__payee_organization_name",
                "schedule_c__lender_organization_name",
                "schedule_d__creditor_organization_name",
                "schedule_e__payee_organization_name",
            ),
            Concat(
                Coalesce(
                    "schedule_a__contributor_last_name",
                    "schedule_b__payee_last_name",
                    "schedule_c__lender_last_name",
                    "schedule_d__creditor_last_name",
                    "schedule_e__payee_last_name",
                ),
                Value(", "),
                Coalesce(
                    "schedule_a__contributor_first_name",
                    "schedule_b__payee_first_name",
                    "schedule_c__lender_first_name",
                    "schedule_d__creditor_first_name",
                    "schedule_e__payee_first_name",
                ),
                output_field=TextField(),
            ),
        ),
    )
    serializer_class = TransactionSerializerBase
    pagination_class = TransactionListPagination
    filter_backends = [filters.OrderingFilter]

    ordering_fields = [
        "line_label_order_key",
        "transaction_type_identifier",
        "memo_code",
        "name",
        "date",
        "amount",
        "aggregate",
        "back_reference_tran_id_number",
    ]
    ordering = ["-created"]

    # Allow requests to filter transactions output based on schedule type by
    # passing a query parameter
    def get_queryset(self):
        queryset = super().get_queryset()
        schedule_filters = self.request.query_params.get("schedules")
        if schedule_filters is not None:
            sched_list = schedule_filters.split(",")
            # All transactions are included by default, here we remove those
            # that are not identified in the schedules query param
            if "A" not in sched_list:
                queryset = queryset.filter(schedule_a__isnull=True)
            if "B" not in sched_list:
                queryset = queryset.filter(schedule_b__isnull=True)
            if "C" not in sched_list:
                queryset = queryset.filter(schedule_c__isnull=True)
            if "C1" not in sched_list:
                queryset = queryset.filter(schedule_c1__isnull=True)
            if "C2" not in sched_list:
                queryset = queryset.filter(schedule_c2__isnull=True)
            if "D" not in sched_list:
                queryset = queryset.filter(schedule_d__isnull=True)
            if "E" not in sched_list:
                queryset = queryset.filter(schedule_e__isnull=True)
        return queryset

    @action(detail=False, methods=["get"], url_path=r"previous/election")
    def previous_election(self, request):
        """Retrieves transaction that comes before this transactions,
        while being in the same group for aggregation"""
        transaction_id = request.query_params.get("transaction_id", None)
        date = request.query_params.get("date", None)
        aggregation_group = request.query_params.get("aggregation_group", None)
        election_code = request.query_params.get("election_code", None)
        candidate_office = request.query_params.get("candidate_office", None)
        candidate_state = request.query_params.get("candidate_state", None)
        candidate_district = request.query_params.get("candidate_district", None)

        missing_params = []
        if not date:
            missing_params.append("date")
        if not aggregation_group:
            missing_params.append("aggregation_group")
        if not election_code:
            missing_params.append("election_code")
        if not candidate_office:
            missing_params.append("candidate_office")
        if (
            candidate_office != Contact.CandidateOffice.PRESIDENTIAL
            and not candidate_state
        ):
            missing_params.append("candidate_state")
        if candidate_office == Contact.CandidateOffice.HOUSE and not candidate_district:
            missing_params.append("candidate_district")

        if len(missing_params) > 0:
            error_msg = (
                "Please provide " + ",".join(missing_params) + " in query params"
            )
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        date = datetime.fromisoformat(date)

        previous_transactions = self.get_queryset().filter(
            ~Q(id=transaction_id or None),
            Q(date__year=date.year),
            Q(date__lte=date),
            Q(aggregation_group=aggregation_group),
            Q(schedule_e__election_code=election_code),
            Q(schedule_e__so_candidate_office=candidate_office),
            Q(schedule_e__so_candidate_state=candidate_state),
            Q(schedule_e__so_candidate_district=candidate_district),
        )

        previous_transaction = previous_transactions.order_by(
            "-date", "-created"
        ).first()

        if previous_transaction:
            serializer = self.get_serializer(previous_transaction)
            return Response(data=serializer.data)

        response = {"message": "No previous transaction found."}
        return Response(response, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["get"], url_path=r"previous/entity")
    def previous_entity(self, request):
        """Retrieves transaction that comes before this transactions,
        while being in the same group for aggregation"""
        transaction_id = request.query_params.get("transaction_id", None)
        contact_1_id = request.query_params.get("contact_1_id", None)
        date = request.query_params.get("date", None)
        aggregation_group = request.query_params.get("aggregation_group", None)

        missing_params = []
        if not contact_1_id:
            missing_params.append("contact_1_id")
        if not date:
            missing_params.append("date")
        if not aggregation_group:
            missing_params.append("aggregation_group")

        if len(missing_params) > 0:
            error_msg = (
                "Please provide " + ",".join(missing_params) + " in query params"
            )
            return Response(
                error_msg,
                status=status.HTTP_400_BAD_REQUEST,
            )

        date = datetime.fromisoformat(date)

        previous_transactions = self.get_queryset().filter(
            ~Q(id=transaction_id or None),
            Q(contact_1_id=contact_1_id),
            Q(date__year=date.year),
            Q(date__lte=date),
            Q(aggregation_group=aggregation_group),
        )

        previous_transaction = previous_transactions.order_by(
            "-date", "-created"
        ).first()

        if previous_transaction:
            serializer = self.get_serializer(previous_transaction)
            return Response(data=serializer.data)

        response = {"message": "No previous transaction found."}
        return Response(response, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["post"], url_path=r"save")
    def create_transaction(self, request):
        return save_transaction(request)

    @action(detail=False, methods=["put"], url_path=r"save/(?P<pk>[^/.]+)")
    def update_transaction(self, request, pk=None):
        return save_transaction(request)

    def create(self, request):
        response = {"message": "Create function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, pk=None):
        response = {"message": "Update function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, pk=None):
        response = {"message": "Update function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)


# clause used to facilitate sorting on name as it's displayed
DISPLAY_NAME_CLAUSE = Coalesce(
    Coalesce(
        "schedule_a__contributor_organization_name",
        "schedule_b__payee_organization_name",
        "schedule_c__lender_organization_name",
        "schedule_d__creditor_organization_name",
        "schedule_e__payee_organization_name",
    ),
    Concat(
        Coalesce(
            "schedule_a__contributor_last_name",
            "schedule_b__payee_last_name",
            "schedule_c__lender_last_name",
            "schedule_d__creditor_last_name",
            "schedule_e__payee_last_name",
        ),
        Value(", "),
        Coalesce(
            "schedule_a__contributor_first_name",
            "schedule_b__payee_first_name",
            "schedule_c__lender_first_name",
            "schedule_d__creditor_first_name",
            "schedule_e__payee_first_name",
        ),
        output_field=TextField(),
    ),
)


class TransactionViewSet2(CommitteeOwnedViewSet, ReportViewMixin):
    serializer_class = TransactionSerializer
    pagination_class = TransactionListPagination
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "line_label_order_key",
        "transaction_type_identifier",
        "memo_code",
        "name",
        "date",
        "amount",
        "aggregate",
        "back_reference_tran_id_number",
    ]
    ordering = ["-created"]

    # Allow requests to filter transactions output based on schedule type by
    # passing a query parameter
    queryset = Transaction.objects.all()

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .alias(
                name=DISPLAY_NAME_CLAUSE,
            )
        )
        schedule_filters = self.request.query_params.get("schedules")
        if schedule_filters is not None:
            schedules_to_include = schedule_filters.split(",")
            # All transactions are included by default, here we remove those
            # that are not identified in the schedules query param
            if "A" not in schedules_to_include:
                queryset = queryset.filter(schedule_a__isnull=True)
            if "B" not in schedules_to_include:
                queryset = queryset.filter(schedule_b__isnull=True)
            if "C" not in schedules_to_include:
                queryset = queryset.filter(schedule_c__isnull=True)
            if "C1" not in schedules_to_include:
                queryset = queryset.filter(schedule_c1__isnull=True)
            if "C2" not in schedules_to_include:
                queryset = queryset.filter(schedule_c2__isnull=True)
            if "D" not in schedules_to_include:
                queryset = queryset.filter(schedule_d__isnull=True)
            if "E" not in schedules_to_include:
                queryset = queryset.filter(schedule_e__isnull=True)

        parent_id = self.request.query_params.get("parent")
        if parent_id:
            queryset = queryset.filter(parent_transaction_id=parent_id)
        return queryset

    def create(self, request, *args, **kwargs):
        with db_transaction.atomic():
            saved_transaction = save_transaction3(request.data, request)
            print(f"creater {saved_transaction.report}")
            print(f"creater {saved_transaction.report_id}")
        return Response(TransactionSerializer().to_representation(saved_transaction))

    def update(self, request, *args, **kwargs):
        with db_transaction.atomic():
            saved_transaction = save_transaction3(request.data, request)
        return Response(TransactionSerializer().to_representation(saved_transaction))

    def partial_update(self, request, pk=None):
        response = {"message": "Update function is not offered in this path."}
        return Response(response, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return response

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return response

    @action(detail=False, methods=["get"], url_path=r"previous/entity")
    def previous_entity(self, request):
        """Retrieves transaction that comes before this transactions,
        while being in the same group for aggregation"""
        transaction_id = request.query_params.get("transaction_id", None)
        contact_1_id = request.query_params.get("contact_1_id", None)
        date = request.query_params.get("date", None)
        aggregation_group = request.query_params.get("aggregation_group", None)

        missing_params = []
        if not contact_1_id:
            missing_params.append("contact_1_id")
        if not date:
            missing_params.append("date")
        if not aggregation_group:
            missing_params.append("aggregation_group")

        if len(missing_params) > 0:
            error_msg = (
                "Please provide " + ",".join(missing_params) + " in query params"
            )
            return Response(
                error_msg,
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self.get_previous(
            transaction_id,
            date,
            aggregation_group,
            contact_1_id,
        )

    @action(detail=False, methods=["get"], url_path=r"previous/election")
    def previous_transaction_by_election(self, request):
        """Retrieves transaction that comes before this transactions,
        while being in the same group for aggregation and the same election"""
        transaction_id = request.query_params.get("transaction_id", None)
        date = request.query_params.get("date", None)
        aggregation_group = request.query_params.get("aggregation_group", None)
        election_code = request.query_params.get("election_code", None)
        candidate_office = request.query_params.get("candidate_office", None)
        candidate_state = request.query_params.get("candidate_state", None)
        candidate_district = request.query_params.get("candidate_district", None)

        missing_params = []
        if not date:
            missing_params.append("date")
        if not aggregation_group:
            missing_params.append("aggregation_group")
        if not election_code:
            missing_params.append("election_code")
        if not candidate_office:
            missing_params.append("candidate_office")
        if (
            candidate_office != Contact.CandidateOffice.PRESIDENTIAL
            and not candidate_state
        ):
            missing_params.append("candidate_state")
        if candidate_office == Contact.CandidateOffice.HOUSE and not candidate_district:
            missing_params.append("candidate_district")

        if len(missing_params) > 0:
            error_msg = (
                "Please provide " + ",".join(missing_params) + " in query params"
            )
            return Response(error_msg, status=status.HTTP_400_BAD_REQUEST)

        return self.get_previous(
            transaction_id,
            date,
            aggregation_group,
            None,
            election_code,
            candidate_office,
            candidate_state,
            candidate_district,
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
            query.filter(Q(contact_1_id=contact_id))
        else:
            query.filter(
                Q(schedule_e__election_code=election_code),
                Q(schedule_e__so_candidate_office=office),
                Q(schedule_e__so_candidate_state=state),
                Q(schedule_e__so_candidate_district=district),
            )
        query.order_by("-date", "-created")
        previous_transaction = query.first()

        if previous_transaction:
            serializer = self.get_serializer(previous_transaction)
            return Response(data=serializer.data)

        response = {"message": "No previous transaction found."}
        return Response(response, status=status.HTTP_404_NOT_FOUND)
