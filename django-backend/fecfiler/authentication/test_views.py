from unittest.mock import Mock
from django.test import RequestFactory, TestCase
from fecfiler.authentication.models import Account
from fecfiler.authentication.views import (
    handle_invalid_login,
    handle_valid_login,
    update_last_login_time,
)

from .views import (
    generate_username,
    login_dot_gov_logout,
    login_redirect,
    logout_redirect,
)


class AuthenticationTest(TestCase):
    fixtures = ["test_accounts"]
    acc = None

    def setUp(self):
        self.user = Account.objects.get(cmtee_id="C12345678")
        self.factory = RequestFactory()
        self.acc = Account.objects.get(email="unit_tester@test.com")

    def test_login_dot_gov_logout_happy_path(self):
        test_state = "test_state"

        mock_request = Mock()
        mock_request.session = Mock()
        mock_request.get_signed_cookie.return_value = test_state

        retval = login_dot_gov_logout(mock_request)
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

    def test_login_dot_gov_login_redirect(self):
        request = self.factory.get("/")
        request.user = self.user
        request.session = {}
        retval = login_redirect(request)
        self.assertEqual(retval.status_code, 302)

    def test_login_dot_gov_logout_redirect(self):
        retval = logout_redirect(self.factory.get("/"))
        self.assertEqual(retval.status_code, 302)

    def test_generate_username(self):
        test_uuid = "test_uuid"
        retval = generate_username(test_uuid)
        self.assertEqual(test_uuid, retval)

    def test_update_login_time(self):
        prev_time = self.acc.last_login
        update_last_login_time(self.acc)
        self.assertNotEqual(self.acc.last_login, prev_time)

    def test_invalid_login(self):
        resp = handle_invalid_login("random_username")
        self.assertEqual(resp.status_code, 401)

    def test_valid_login(self):
        resp = handle_valid_login(self.acc)
        self.assertEqual(resp.status_code, 200)
