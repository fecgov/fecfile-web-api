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
            f3x_summary = request.query_params.get("f3x_summary")

        if f3x_summary == None:
            queryset = self.queryset
        else:
            if isinstance(queryset, QuerySet):
                queryset = queryset.all().filter(
                    f3x_summary_form=f3x_summary
                )
        return queryset

    queryset = SchATransaction.objects.all().order_by("-id")
    serializer_class = SchATransactionSerializer
    permission_classes = []
