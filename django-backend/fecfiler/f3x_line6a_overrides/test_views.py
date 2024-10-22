from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient

from fecfiler.user.models import User


class F3xLine6aOverrideViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee", "test_f3x_line6a_overrides"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def test_create_f3x_line6a_overrides_happy_path(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        test_post_data = {
            "L6a_cash_on_hand_jan_1_ytd": 333.25,
            "L6a_year_for_above_ytd": "2024",
        }

        response = client.post(
            "/api/v1/f3x_line6a_overrides/", test_post_data, secure=True
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["L6a_cash_on_hand_jan_1_ytd"], "333.25")
        self.assertEqual(response.data["L6a_year_for_above_ytd"], "2024")

    def test_update_f3x_line6a_overrides_happy_path(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.get(
            "/api/v1/f3x_line6a_overrides/c113e49f-d3b2-42d0-9128-13a70d2b936f/",
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["L6a_cash_on_hand_jan_1_ytd"], "123.45")
        self.assertEqual(response.data["L6a_year_for_above_ytd"], "2021")

        test_put_data = {
            "L6a_cash_on_hand_jan_1_ytd": 678.90,
            "L6a_year_for_above_ytd": 2021,
        }

        response = client.put(
            "/api/v1/f3x_line6a_overrides/c113e49f-d3b2-42d0-9128-13a70d2b936f/",
            test_put_data,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["L6a_cash_on_hand_jan_1_ytd"], "678.90")
        self.assertEqual(response.data["L6a_year_for_above_ytd"], "2021")
