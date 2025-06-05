from datetime import date, timedelta
from fecfiler.test.viewset_test import FecfilerViewSetTest
from fecfiler.user.views import UserViewSet


class UserViewSetTest(FecfilerViewSetTest):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        super().setUp()

    def test_get_current_user_unsigned_security_consent(self):
        response = self.send_viewset_get_request(
            "/api/v1/users/get_current/",
            UserViewSet,
            "get_current",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["first_name"], "First")
        self.assertEqual(response.data["last_name"], "Last")
        self.assertEqual(response.data["email"], "test@fec.gov")
        self.assertEqual(response.data["security_consented"], False)

    def test_get_current_user_signed_ephemeral_security_consent(self):
        test_put_data = {
            "first_name": "test_first_name_updated",
            "last_name": "test_last_name_updated",
            "email": "test@fec.gov",
            "consent_for_one_year": False,
        }
        response = self.send_viewset_put_request(
            "/api/v1/users/update_current/",
            test_put_data,
            UserViewSet,
            "update_current",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["first_name"], "test_first_name_updated")
        self.assertEqual(response.data["last_name"], "test_last_name_updated")
        self.assertEqual(response.data["email"], "test@fec.gov")
        self.assertEqual(response.data["security_consented"], True)
        self.assertNotEqual(self.default_user.security_consent_exp_date, date.today())

    def test_get_current_user_signed_annual_security_consent(self):
        test_put_data = {
            "first_name": "test_first_name_updated2",
            "last_name": "test_last_name_updated2",
            "email": "test@fec.gov",
            "consent_for_one_year": True,
        }

        response = self.send_viewset_put_request(
            "/api/v1/users/update_current/",
            test_put_data,
            UserViewSet,
            "update_current",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["first_name"], "test_first_name_updated2")
        self.assertEqual(response.data["last_name"], "test_last_name_updated2")
        self.assertEqual(response.data["email"], "test@fec.gov")
        self.assertEqual(response.data["security_consented"], True)
        self.assertEqual(
            self.default_user.security_consent_exp_date,
            date.today() + timedelta(days=365),
        )
