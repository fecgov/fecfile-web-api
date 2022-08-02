from rest_framework import viewsets
from django.db.models.query import QuerySet
import logging

logger = logging.getLogger(__name__)


class CommitteeOwnedViewSet(viewsets.ModelViewSet):
    """ModelViewSet for models using CommitteeOwnedModel
    Inherit this view set to filter the queryset by the user's committee
    """

    def get_queryset(self):
        committee_id = self.request.user.cmtee_id
        queryset = super().get_queryset()
        return queryset.filter(committee_account__committee_id=committee_id)
