from rest_framework import viewsets
from .models import SchATransaction
from .serializers import SchATransactionSerializer


class SchATransactionViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.

    Note that this ViewSet inherits from CommitteeOwnedViewSet
    The queryset will be further limmited by the user's committee
    in CommitteeOwnedViewSet's implementation of get_queryset()
    """

    queryset = SchATransaction.objects.all().order_by("-id")
    serializer_class = SchATransactionSerializer
    permission_classes = []
