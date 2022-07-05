from rest_framework import filters
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from .models import SchATransaction
from django.db.models.query import QuerySet
from .serializers import SchATransactionSerializer
from django.db.models import TextField, Value
from django.db.models.functions import Concat, Coalesce


class SchATransactionViewSet(CommitteeOwnedViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Note that this ViewSet inherits from CommitteeOwnedViewSet
    The queryset will be further limmited by the user's committee
    in CommitteeOwnedViewSet's implementation of get_queryset()
    """

    queryset = SchATransaction.objects.select_related("parent_transaction_id").alias(
        contributor_name=Coalesce(
            "contributor_organization_name",
            Concat(
                "contributor_last_name",
                Value(", "),
                "contributor_first_name",
                output_field=TextField(),
            ),
        )
    ).all()
    """QuerySet: all schedule a transactions with an aditional contributor_name field"""

    def get_queryset(self):
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method." % self.__class__.__name__
        )

        report_id = None
        if self.request is not None:
            report_id = self.request.query_params.get("report_id")

        queryset = super.get_queryset()
        if report_id is not None and report_id != '':
            if isinstance(queryset, QuerySet):
                queryset = SchATransaction.objects.all().filter(
                    report_id=report_id
                )
        return queryset

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
    ordering = ["-id"]
