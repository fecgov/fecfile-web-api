from .models import MemoText
from .serializers import MemoTextSerializer
from django.db.models.query import QuerySet
from fecfiler.committee_accounts.views import CommitteeOwnedViewSet

TRANSACTION_ID_NUMBER_FIELD = "transaction_id_number"


class MemoTextViewSet(CommitteeOwnedViewSet):
    def create(self, request, *args, **kwargs):
        request_report_id = request.data["report_id"]
        next_transaction_id_number = self.get_next_transaction_id_number(
            request_report_id
        )
        request.data[TRANSACTION_ID_NUMBER_FIELD] = next_transaction_id_number
        return super().create(request, args, kwargs)

    def get_next_transaction_id_number(self, report_id):
        memo_text_tid_base = "REPORT_MEMO_TEXT_"
        memo_text_xid_dict = (
            MemoText.objects.filter(report_id=report_id)
            .values(TRANSACTION_ID_NUMBER_FIELD)
            .order_by(f"-{TRANSACTION_ID_NUMBER_FIELD}")
            .first()
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
    queryset = MemoText.objects.all().order_by("-id")

    def get_queryset(self):
        report_id = None
        if self.request is not None:
            report_id = self.request.query_params.get("report_id")

        queryset = MemoText.objects.all().order_by(f"-{TRANSACTION_ID_NUMBER_FIELD}")
        if isinstance(queryset, QuerySet):
            queryset = (
                MemoText.objects.all().filter(report_id=report_id).order_by("-id")
            )
        return queryset

    serializer_class = MemoTextSerializer
    pagination_class = None
