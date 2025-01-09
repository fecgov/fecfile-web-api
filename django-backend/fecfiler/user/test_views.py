from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient
from datetime import date, timedelta

from fecfiler.user.models import User


class UserViewSetTest(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.factory = RequestFactory()

    def test_get_current_user_unsigned_security_consent(self):
        client = APIClient()
        client.force_authenticate(user=self.user)

        response = client.get("/api/v1/users/get_current/", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["first_name"], "First")
        self.assertEqual(response.data["last_name"], "Last")
        self.assertEqual(response.data["email"], "test@fec.gov")
        self.assertEqual(response.data["security_consented"], False)

    def test_get_current_user_signed_ephemeral_security_consent(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        test_put_data = {
            "first_name": "test_first_name_updated",
            "last_name": "test_last_name_updated",
            "email": "test@fec.gov",
            "consent_for_one_year": False,
        }

        client.put("/api/v1/users/update_current/", test_put_data, secure=True)
        response = client.get("/api/v1/users/get_current/", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["first_name"], "test_first_name_updated")
        self.assertEqual(response.data["last_name"], "test_last_name_updated")
        self.assertEqual(response.data["email"], "test@fec.gov")
        self.assertEqual(response.data["security_consented"], True)
        self.assertNotEqual(self.user.security_consent_exp_date, date.today())

    def test_get_current_user_signed_annual_security_consent(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        test_put_data = {
            "first_name": "test_first_name_updated2",
            "last_name": "test_last_name_updated2",
            "email": "test@fec.gov",
            "consent_for_one_year": True,
        }

        client.put("/api/v1/users/update_current/", test_put_data, secure=True)
        response = client.get("/api/v1/users/get_current/", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["first_name"], "test_first_name_updated2")
        self.assertEqual(response.data["last_name"], "test_last_name_updated2")
        self.assertEqual(response.data["email"], "test@fec.gov")
        self.assertEqual(response.data["security_consented"], True)
        self.assertEqual(
            self.user.security_consent_exp_date, date.today() + timedelta(days=365)
        )
