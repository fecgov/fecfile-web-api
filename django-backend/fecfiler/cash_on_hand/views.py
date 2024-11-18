from rest_framework.response import Response
from rest_framework.decorators import action
from fecfiler.committee_accounts.views import CommitteeOwnedViewMixin
from .serializers import CashOnHandYearlySerializer
from .models import CashOnHandYearly
import logging

logger = logging.getLogger(__name__)


class CashOnHandYearlyViewSet(CommitteeOwnedViewMixin):
    """

    Note that this ViewSet inherits from CommitteeOwnedViewMixin
    The queryset will be further limited by the user's committee
    in CommitteeOwnedViewMixin's implementation of get_queryset()
    """

    queryset = CashOnHandYearly.objects
    serializer_class = CashOnHandYearlySerializer
    pagination_class = None

    @action(detail=False, methods=["get", "post"], url_path=r"year/(?P<year>\d+)")
    def cash_on_hand_for_year(self, request, year):
        if request.method == "GET":
            return self.get_cash_on_hand_for_year(request, year)
        elif request.method == "POST":
            return self.set_cash_on_hand_for_year(request, year)

    def get_cash_on_hand_for_year(self, request, year):
        cash_on_hand = self.get_queryset().filter(year=year).first()
        if cash_on_hand is None:
            return Response(status=404)
        serializer = self.get_serializer(cash_on_hand)
        return Response(serializer.data)

    def set_cash_on_hand_for_year(self, request, year):
        new_cash_on_hand = request.data.get("cash_on_hand")
        committee_uuid = self.get_committee_uuid()
        if new_cash_on_hand is None:
            return Response("cash_on_hand is required", status=400)
        cash_on_hand_record = self.get_queryset().filter(year=year).first()
        if cash_on_hand_record is None:
            cash_on_hand_record = CashOnHandYearly.objects.create(
                committee_account_id=committee_uuid,
                year=year,
                cash_on_hand=new_cash_on_hand,
            )
        else:
            cash_on_hand_record.cash_on_hand = new_cash_on_hand
            cash_on_hand_record.save()

        serializer = self.get_serializer(cash_on_hand_record)
        return Response(serializer.data)
