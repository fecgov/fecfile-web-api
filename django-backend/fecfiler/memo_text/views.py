from .models import MemoText
from .serializers import MemoTextSerializer
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet
from fecfiler.f3x_summaries.views import ReportViewMixin

TRANSACTION_ID_NUMBER_FIELD = "transaction_id_number"


class MemoTextViewSet(CommitteeOwnedViewSet, ReportViewMixin):
    def create(self, request, *args, **kwargs):
        request.data[
            TRANSACTION_ID_NUMBER_FIELD
        ] = self.get_next_transaction_id_number()
        return super().create(request, args, kwargs)

    def get_next_transaction_id_number(self):
        memo_text_tid_base = "REPORT_MEMO_TEXT_"
        memo_text_xid_dict = (
            self.get_queryset().values(TRANSACTION_ID_NUMBER_FIELD).first()
        )
        if (
            memo_text_xid_dict is None
            or memo_text_xid_dict[TRANSACTION_ID_NUMBER_FIELD] is None
        ):
            return memo_text_tid_base + "1"
        else:
            tokens = memo_text_xid_dict[TRANSACTION_ID_NUMBER_FIELD].split("_")
            memo_counter = tokens[len(tokens) - 1]
            return memo_text_tid_base + str(int(memo_counter) + 1)

    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = MemoText.objects.all()

    serializer_class = MemoTextSerializer
    pagination_class = None
