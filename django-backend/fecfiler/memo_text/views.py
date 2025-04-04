from .models import MemoText
from .serializers import MemoTextSerializer
from fecfiler.reports.views import ReportViewMixin
from rest_framework.viewsets import ModelViewSet


class MemoTextViewSet(ReportViewMixin, ModelViewSet):
    def get_queryset(self):
        memos = super().get_queryset()
        query_params = self.request.query_params.keys()
        if "report_id" in query_params:
            report_id = self.request.query_params["report_id"]
            memos = memos.filter(report_id=report_id, transaction_uuid=None)

        return memos

    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = MemoText.objects.all()

    serializer_class = MemoTextSerializer
    pagination_class = None
