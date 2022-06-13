from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from .models import Account
from .serializers import AccountSerializer
import logging

logger = logging.getLogger(__name__)


class AccountViewSet(GenericViewSet, ListModelMixin):
    """
        The Account ViewSet allows the user to retrieve the users in the same committee

        The CommitteeOwnedViewset could not be inherited due to the different structure
        of a user object versus other objects.
            (IE - having a "cmtee_id" field instead of "committee_id")
    """
    queryset = Account.objects.all().order_by("id")
    serializer_class = AccountSerializer

    def get_queryset(self):
        return self.queryset.filter(cmtee_id=self.request.user.cmtee_id)
