from rest_framework import viewsets
import structlog

logger = structlog.get_logger(__name__)


class CommitteeOwnedViewSet(viewsets.ModelViewSet):
    """ModelViewSet for models using CommitteeOwnedModel
    Inherit this view set to filter the queryset by the user's committee
    """

    def get_queryset(self):
        committee_id = self.request.user.cmtee_id
        queryset = super().get_queryset()
        structlog.contextvars.bind_contextvars(
            committee_id=self.request.user.cmtee_id
        )
        return queryset.filter(committee_account__committee_id=committee_id)
