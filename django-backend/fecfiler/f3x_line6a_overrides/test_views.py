from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient

from fecfiler.user.models import User


class F3xLine6aOverrideViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee", "test_f3x_line6a_overrides"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def test_get_f3x_line6a_overrides_by_year_happy_path(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.get(
            "/api/v1/f3x_line6a_overrides/?year=2019",
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["year"], "2019")
        self.assertEqual(response.data[0]["cash_on_hand"], "543.21")

    def test_create_f3x_line6a_overrides_happy_path(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        test_post_data = {
            "year": "2024",
            "cash_on_hand": 333.25,
        }

        response = client.post(
            "/api/v1/f3x_line6a_overrides/", test_post_data, secure=True
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["year"], "2024")
        self.assertEqual(response.data["cash_on_hand"], "333.25")

    def test_update_f3x_line6a_overrides_happy_path(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.get(
            "/api/v1/f3x_line6a_overrides/c113e49f-d3b2-42d0-9128-13a70d2b936f/",
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["year"], "2021")
        self.assertEqual(response.data["cash_on_hand"], "123.45")

        test_put_data = {
            "year": 2021,
            "cash_on_hand": 678.90,
        }

        response = client.put(
            "/api/v1/f3x_line6a_overrides/c113e49f-d3b2-42d0-9128-13a70d2b936f/",
            test_put_data,
            secure=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["year"], "2021")
        self.assertEqual(response.data["cash_on_hand"], "678.90")
