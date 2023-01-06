import logging

from rest_framework import filters
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.f3x_summaries.views import ReportViewMixin


logger = logging.getLogger(__name__)


class TransactionViewSetBase(CommitteeOwnedViewSet, ReportViewMixin):
    """ """

    filter_backends = [filters.OrderingFilter]
    ordering = ["-created"]
