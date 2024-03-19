from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient

from fecfiler.user.models import User


class UserViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def test_get_current_user_happy_path(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.get("/api/v1/users/current/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["first_name"], "First")
        self.assertEqual(response.data["last_name"], "Last")
        self.assertEqual(response.data["email"], "test@fec.gov")
        self.assertEqual(response.data["security_consent_exp_date"], "2024-03-12")

    def test_update_current_user_happy_path(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        test_put_data = {
            "first_name": "test_first_name_updated",
            "last_name": "test_last_name_updated",
            "email": "test@fec.gov",
            "security_consent_exp_date": "2025-03-12",
        }

        response = client.put("/api/v1/users/current/", test_put_data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["first_name"], "test_first_name_updated")
        self.assertEqual(response.data["last_name"], "test_last_name_updated")
        self.assertEqual(response.data["email"], "test@fec.gov")
        self.assertEqual(response.data["security_consent_exp_date"], "2025-03-12")
