from .models import MemoText
from django.db.models import Q
from .serializers import MemoTextSerializer
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.f3x_summaries.views import ReportViewMixin

TRANSACTION_ID_NUMBER_FIELD = "transaction_id_number"
MEMO_TEXT_ID_BASE = "REPORT_MEMO_TEXT_"


class MemoTextViewSet(CommitteeOwnedViewSet, ReportViewMixin):
    """
    def create(self, request, *args, **kwargs):
        request.data[
            TRANSACTION_ID_NUMBER_FIELD
        ] = self.get_next_transaction_id_number()
        return super().create(request, args, kwargs)
    """

    def get_queryset(self):
        memos = MemoText.objects.all()
        print("\n\n----\n",self.request.query_params.keys(),"\n----\n\n")
        query_params = self.request.query_params.keys()
        if ("report_id" in query_params):
            report_id = self.request.query_params["report_id"]
            memos = memos.filter(
                report_id=report_id,
                transaction_uuid=None
            )

        return memos

        filter = (
            (
                self.request.query_params.get(TRANSACTION_ID_NUMBER_FIELD)
                or self.request.data.get(TRANSACTION_ID_NUMBER_FIELD)
            )
            if self.request
            else None
        )
        queryset = super().get_queryset()
        return (
            queryset.filter(Q((TRANSACTION_ID_NUMBER_FIELD, filter)))
            if filter
            else queryset
        )

    def get_next_transaction_id_number(self):
        latest_memo = (
            self.get_queryset().values(TRANSACTION_ID_NUMBER_FIELD, "report_id").first()
        )
        if latest_memo and latest_memo.get(TRANSACTION_ID_NUMBER_FIELD):
            tokens = latest_memo.get(TRANSACTION_ID_NUMBER_FIELD).split("_")
            return MEMO_TEXT_ID_BASE + str(int(tokens[-1]) + 1)
        else:
            return MEMO_TEXT_ID_BASE + "1"

    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = MemoText.objects.all()

    serializer_class = MemoTextSerializer
    pagination_class = None
