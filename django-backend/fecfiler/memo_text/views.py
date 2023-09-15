from .models import MemoText
from .serializers import MemoTextSerializer
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.reports.f3x_report.views import ReportViewMixin


class MemoTextViewSet(CommitteeOwnedViewSet, ReportViewMixin):
    def get_queryset(self):
        memos = MemoText.objects.all()
        query_params = self.request.query_params.keys()
        if ("report_id" in query_params):
            report_id = self.request.query_params["report_id"]
            memos = memos.filter(
                report_id=report_id,
                transaction_uuid=None
            )

        return memos

    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = MemoText.objects.all()

    serializer_class = MemoTextSerializer
    pagination_class = None
