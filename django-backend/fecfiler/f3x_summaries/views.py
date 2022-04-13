from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from .models import F3XSummary
from .serializers import F3XSummarySerializer


class F3XSummaryViewSet(CommitteeOwnedViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Note that this ViewSet inherits from CommitteeOwnedViewSet
    The queryset will be further limmited by the user's committee
    in CommitteeOwnedViewSet's implementation of get_queryset()
    """

    queryset = F3XSummary.objects.all().order_by("-id")
    serializer_class = F3XSummarySerializer
    permission_classes = []
