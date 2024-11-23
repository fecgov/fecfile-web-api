from django.test import RequestFactory, TestCase
from ..views import CashOnHandYearlyViewSet
from ..models import CashOnHandYearly
from fecfiler.committee_accounts.models import CommitteeAccount
from .utils import create_cash_on_hand_yearly
from rest_framework.test import force_authenticate

from fecfiler.user.models import User


class CashOnHandYearlyViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")

        self.committee = CommitteeAccount.objects.get(committee_id="C01234567")
        self.factory = RequestFactory()

    def test_no_override(self):
        request = self.factory.get("/api/v1/cash_on_hand/year/2024/")
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        other_committee = CommitteeAccount.objects.create(committee_id="C00000001")
        create_cash_on_hand_yearly(other_committee, "2024", 1)
        response = CashOnHandYearlyViewSet.as_view({"get": "cash_on_hand_for_year"})(
            request, year="2024"
        )
        self.assertEqual(response.status_code, 404)

    def test_get_override(self):
        request = self.factory.get("/api/v1/cash_on_hand/year/2024/")
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        create_cash_on_hand_yearly(self.committee, "2024", 1)
        response = CashOnHandYearlyViewSet.as_view({"get": "cash_on_hand_for_year"})(
            request, year="2024"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cash_on_hand"], "1.00")

    def test_set_override(self):
        request = self.factory.post(
            "/api/v1/cash_on_hand/year/2024/", {"cash_on_hand": 2}
        )
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        force_authenticate(request, self.user)
        response = CashOnHandYearlyViewSet.as_view({"post": "cash_on_hand_for_year"})(
            request, year="2024"
        )
        self.assertEqual(response.status_code, 200)
        cash_on_hand = CashOnHandYearly.objects.get(
            committee_account=self.committee, year="2024"
        )
        self.assertEqual(cash_on_hand.cash_on_hand, 2)
        self.assertEqual(response.data["cash_on_hand"], "2.00")

    def test_set_override_multiple_cmtes(self):
        new_committee = CommitteeAccount.objects.create(
            committee_id="C00000000"
        )

        for committee in (self.committee, new_committee):
            request = self.factory.post(
                "/api/v1/cash_on_hand/year/2024/", {"cash_on_hand": 2}
            )
            request.user = self.user
            request.session = {
                "committee_uuid": str(committee.id),
                "committee_id": str(committee.committee_id),
            }
            force_authenticate(request, self.user)
            response = CashOnHandYearlyViewSet.as_view({"post": "cash_on_hand_for_year"})(
                request, year="2024"
            )
            self.assertEqual(response.status_code, 200)
            cash_on_hand = CashOnHandYearly.objects.get(
                committee_account=committee, year="2024"
            )
            self.assertEqual(cash_on_hand.cash_on_hand, 2)
            self.assertEqual(response.data["cash_on_hand"], "2.00")
