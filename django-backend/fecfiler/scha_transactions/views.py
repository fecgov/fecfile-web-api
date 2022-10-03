from rest_framework import filters
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.f3x_summaries.views import ReportViewMixin
from .models import SchATransaction
from .serializers import SchATransactionParentSerializer
from django.db.models import TextField, Value
from django.db.models.functions import Concat, Coalesce
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

    serializer_class = SchATransactionParentSerializer
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
    ordering = ["-id"]
