from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from .models import SchATransaction
from django.db.models.query import QuerySet
from .serializers import SchATransactionSerializer


class SchATransactionViewSet(CommitteeOwnedViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Note that this ViewSet inherits from CommitteeOwnedViewSet
    The queryset will be further limmited by the user's committee
    in CommitteeOwnedViewSet's implementation of get_queryset()
    """

    def get_queryset(self):
        assert self.queryset is not None, (
            "'%s' should either include a `queryset` attribute, "
            "or override the `get_queryset()` method." % self.__class__.__name__
        )

        f3x_summary = None
        request = self.context.get("request", None)
        if request:
            f3x_summary_id = request.query_params.get("f3x_summary_id")

        if f3x_summary_id == None:
            queryset = self.queryset
        else:
            if isinstance(queryset, QuerySet):
                queryset = queryset.all().filter(
                    scha_transaction__f3x_summary_id=f3x_summary_id
                )
        return queryset

    queryset = SchATransaction.objects.all().order_by("-id")
    serializer_class = SchATransactionSerializer
    permission_classes = []
