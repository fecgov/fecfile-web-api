from rest_framework import viewsets
from fecfiler.authentication.authenticate_login import get_logged_in_user
import logging

logger = logging.getLogger(__name__)


class CommitteeOwnedViewSet(viewsets.ModelViewSet):
    """ModelViewSet for models using CommitteeOwnedModel
    Inherit this view set to filter the queryset by the user's committee
    """

    def get_queryset(self):
        user = get_logged_in_user(self.request)
        committee_id = user.cmtee_id
        queryset = super().get_queryset()
        return queryset.filter(committee_account__committee_id=committee_id)
