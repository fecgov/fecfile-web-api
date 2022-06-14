from rest_framework import filters
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import ListModelMixin
from django.db.models import Value, CharField
from django.db.models.functions import Concat
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
    queryset = Account.objects.annotate(
        name=Concat('first_name', Value(', '), 'last_name', output_field=CharField())
    ).all()
    serializer_class = AccountSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = [
                      "last_name",
                      "first_name",
                      "id",
                      "email",
                      "role",
                      "is_active",
                      "name"
    ]
    ordering = ["name"]

    def get_queryset(self):
        return self.queryset.filter(cmtee_id=self.request.user.cmtee_id)
