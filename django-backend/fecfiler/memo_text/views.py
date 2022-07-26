from .models import MemoText
from .serializers import MemoTextSerializer
from django.db.models.query import QuerySet
from rest_framework import viewsets


class MemoTextViewSet(viewsets.ModelViewSet):

    def create(self, request, *args, **kwargs):
        request_report_id = request.data['report_id']
        next_transaction_id_number = self.get_next_transaction_id_number(
            request_report_id)
        request.data['transaction_id_number'] = next_transaction_id_number
        return super().create(request, args, kwargs)

    def get_next_transaction_id_number(self, report_id):
        transaction_id_number_field_name = 'transaction_id_number'
        memo_text_tid_base = 'REPORT_MEMO_TEXT_'
        memo_text_xid_dict = MemoText.objects.filter(
            report_id=report_id).values(
            transaction_id_number_field_name).order_by('-id').first()
        if (memo_text_xid_dict is None or
                memo_text_xid_dict[transaction_id_number_field_name] is None):
            return memo_text_tid_base + '1'
        else:
            tokens = memo_text_xid_dict[
                transaction_id_number_field_name].split('_')
            memo_counter = tokens[len(tokens)-1]
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

        queryset = MemoText.objects.all().order_by("-id")
        if report_id is not None and report_id != '':
            if isinstance(queryset, QuerySet):
                queryset = MemoText.objects.all().filter(
                    report_id=report_id
                ).order_by("-id")
        return queryset

    serializer_class = MemoTextSerializer
    pagination_class = None
