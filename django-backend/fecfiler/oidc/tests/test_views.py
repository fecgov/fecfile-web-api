from unittest.mock import Mock, patch
from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model
from django.contrib.sessions.middleware import SessionMiddleware
from unittest.mock import MagicMock

from fecfiler.oidc.views import (
    login_redirect,
    logout_redirect,
    oidc_authenticate,
    oidc_callback,
    oidc_logout,
)


import time

UserModel = get_user_model()


class MockUser:
    is_authenticated = True
    is_active = True


class OidcTest(TestCase):
    fixtures = ["C01234567_user_and_committee"]
    user = MockUser()

    def get_request(self, uri):
        request = self.factory.get(uri)
        request.user = self.user
        self.middleware = SessionMiddleware(MagicMock())
        self.middleware.process_request(request)
        request.session.save()
        return request

    def setUp(self):
        self.factory = RequestFactory()

    def xtest_login_dot_gov_logout_happy_path(self):
        test_state = "test_state"

        mock_request = Mock()
        mock_request.session = Mock()
        mock_request.get_signed_cookie.return_value = test_state

        retval = oidc_logout(mock_request)
        self.maxDiff = None
        self.assertEqual(
            retval,
            (
                "https://idp.int.identitysandbox.gov"
                "/openid_connect/logout?"
                "client_id=None"
                "&post_logout_redirect_uri=None"
                "&state=test_state"
            ),
        )

    def test_login_redirect(self):
        request = self.factory.get("/")
        request.user = self.user
        request.session = {}
        retval = login_redirect(request)
        self.assertEqual(retval.status_code, 302)

    @patch("fecfiler.oidc.views.logout")
    def test_logout_redirect(self, logout_mock):
        retval = logout_redirect(self.factory.get("/"))
        self.assertEqual(retval.status_code, 302)

    def test_oidc_authenticate(self):
        request = self.factory.get("/")
        request.user = self.user
        request.session = {
            "oidc_states": {
                "test_state_1_key": {"nonce": "test_nonce_1", "added_on": time.time()},
                "test_state_2_key": {"nonce": "test_nonce_2", "added_on": time.time()},
                "test_state_3_key": {"nonce": "test_nonce_3", "added_on": time.time()},
            }
        }
        retval = oidc_authenticate(request)
        self.assertEqual(retval.status_code, 302)
        self.assertIsNotNone(retval.cookies.get("oidc_state"))

    def test_oidc_callback_error(self):
        test_state = "test_state"
        request = self.get_request(f"/?error=true&state={test_state}")
        request.session["oidc_states"] = {
            test_state: {"nonce": "test_nonce_1", "added_on": time.time()},
        }
        request.user = self.user

        retval = oidc_callback(request)
        self.assertEqual(retval.status_code, 302)
        self.assertEqual(len(request.session.get("oidc_states")), 0)

    def test_oidc_callback_session_states_not_found(self):
        test_code = "test_code"
        test_state = "test_state"
        request = self.get_request(f"/?code={test_code}&state={test_state}")

        retval = oidc_callback(request)
        self.assertEqual(retval.status_code, 500)

    @patch("fecfiler.oidc.utils.authenticate")
    @patch("fecfiler.oidc.utils.login")
    def test_oidc_callback_happy_path(self, login_mock, authenticate_mock):
        test_code = "test_code"
        test_state = "test_state"

        authenticate_mock.return_value = self.user

        request = self.get_request(f"/?code={test_code}&state={test_state}")
        request.session["oidc_states"] = {
            test_state: {"nonce": "test_nonce_1", "added_on": time.time()},
        }

        retval = oidc_callback(request)
        self.assertEqual(retval.status_code, 302)

    def test_oidc_logout_happy_path(self):
        auth_request = self.factory.get("/")
        auth_request.user = self.user
        auth_request.session = {
            "oidc_states": {
                "test_state_1_key": {"nonce": "test_nonce_1", "added_on": time.time()},
                "test_state_2_key": {"nonce": "test_nonce_2", "added_on": time.time()},
                "test_state_3_key": {"nonce": "test_nonce_3", "added_on": time.time()},
            }
        }
        auth_response = oidc_authenticate(auth_request)

        request = self.get_request("/")
        request.COOKIES["oidc_state"] = auth_response.cookies["oidc_state"].value

        retval = oidc_logout(request)
        self.assertEqual(retval.status_code, 302)
