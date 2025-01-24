from rest_framework import filters
import structlog

logger = structlog.get_logger(__name__)


class CommitteeOwnedFilterBackend(filters.BaseFilterBackend):
    """FilterBackend for viewsets using ReportViewSet
    Providing a queryset filter to limit by committee UUID
    """

    def get_committee_uuid(self, request):
        committee_uuid = request.session["committee_uuid"]
        if not committee_uuid:
            raise SuspiciousSession("session has invalid committee_uuid")
        return committee_uuid

    def get_committee_id(self, request):
        committee_id = request.session["committee_id"]
        if not committee_id:
            raise SuspiciousSession("session has invalid committee_id")
        return committee_id

    def filter_queryset(self, request, queryset, view):
        committee_uuid = self.get_committee_uuid(request)
        committee_id = self.get_committee_id(request)
        structlog.contextvars.bind_contextvars(
            committee_id=committee_id, committee_uuid=committee_uuid
        )
        logger.info(f'Exiting filter_queryset')
        return queryset.filter(committee_account_id=committee_uuid)
