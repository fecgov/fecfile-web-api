from datetime import datetime
from rest_framework import filters
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.f3x_summaries.views import ReportViewMixin
from .models import SchATransaction
from .serializers import SchATransactionSerializer
from django.db.models import TextField, Value, Q
from django.db.models.functions import Concat, Coalesce
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

import logging

logger = logging.getLogger(__name__)


class SchATransactionViewSet(CommitteeOwnedViewSet, ReportViewMixin):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Note that this ViewSet inherits from CommitteeOwnedViewSet
    The queryset will be further limmited by the user's committee
    in CommitteeOwnedViewSet's implementation of get_queryset()
    """

    queryset = (
        SchATransaction.objects.select_related("parent_transaction")
        .alias(
            contributor_name=Coalesce(
                "contributor_organization_name",
                Concat(
                    "contributor_last_name",
                    Value(", "),
                    "contributor_first_name",
                    output_field=TextField(),
                ),
            )
        )
        .all()
    )
    """QuerySet: all schedule a transactions with an aditional contributor_name field"""

    serializer_class = SchATransactionSerializer
    permission_classes = []
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
        "id",
        "transaction_type_identifier",
        "contributor_name",
        "contribution_date",
        "memo_code",
        "contribution_amount",
    ]
    ordering = ["-created"]

    @action(detail=False, methods=["get"])
    def previous(self, request):
        contact_id = request.query_params.get("contact_id", None)
        contribution_date = request.query_params.get("contribution_date", None)
        if not (contact_id and contribution_date):
            return Response(
                "Please provide contact_id and contribution_date in query params.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        contribution_date = datetime.fromisoformat(contribution_date)

        previous_transaction = (
            self.get_queryset()
            .filter(
                Q(contact_id=contact_id),
                Q(contribution_date__year=contribution_date.year),
                Q(contribution_date__lt=contribution_date),
            )
            .order_by("-created")
            .first()
        )

        logger.error(f"AHOY: {previous_transaction}")

        serializer = self.get_serializer(previous_transaction)
        return Response(data=serializer.data)
