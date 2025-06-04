from ..views import CashOnHandYearlyViewSet
from ..models import CashOnHandYearly
from fecfiler.committee_accounts.models import CommitteeAccount
from .utils import create_cash_on_hand_yearly
from fecfiler.test.viewset_test import FecfilerViewSetTest

from fecfiler.user.models import User


class CashOnHandYearlyViewSetTest(FecfilerViewSetTest):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        super().setUp()
        self.committee = CommitteeAccount.objects.get(committee_id="C01234567")

    def test_no_override(self):
        other_committee = CommitteeAccount.objects.create(committee_id="C00000001")
        create_cash_on_hand_yearly(other_committee, "2024", 1)
        response = self.send_viewset_get_request_for_default(
            "/api/v1/cash_on_hand/year/2024/",
            CashOnHandYearlyViewSet,
            "cash_on_hand_for_year",
            year="2024",
        )
        self.assertEqual(response.status_code, 404)

    def test_get_override(self):
        create_cash_on_hand_yearly(self.committee, "2024", 1)
        response = self.send_viewset_get_request_for_default(
            "/api/v1/cash_on_hand/year/2024/",
            CashOnHandYearlyViewSet,
            "cash_on_hand_for_year",
            year="2024",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cash_on_hand"], "1.00")

    def test_set_override(self):
        response = self.send_viewset_post_request_for_default(
            "/api/v1/cash_on_hand/year/2024/",
            {"cash_on_hand": 2},
            CashOnHandYearlyViewSet,
            "cash_on_hand_for_year",
            year="2024",
        )
        self.assertEqual(response.status_code, 200)
        cash_on_hand = CashOnHandYearly.objects.get(
            committee_account=self.committee, year="2024"
        )
        self.assertEqual(cash_on_hand.cash_on_hand, 2)
        self.assertEqual(response.data["cash_on_hand"], "2.00")

    def test_set_override_multiple_cmtes(self):
        new_committee = CommitteeAccount.objects.create(committee_id="C00000000")

        for committee in (self.committee, new_committee):
            response = self.send_viewset_post_request_for_committee(
                "/api/v1/cash_on_hand/year/2024/",
                {"cash_on_hand": 2},
                CashOnHandYearlyViewSet,
                "cash_on_hand_for_year",
                committee=committee,
                year="2024",
            )
            self.assertEqual(response.status_code, 200)
            cash_on_hand = CashOnHandYearly.objects.get(
                committee_account=committee, year="2024"
            )
            self.assertEqual(cash_on_hand.cash_on_hand, 2)
            self.assertEqual(response.data["cash_on_hand"], "2.00")
