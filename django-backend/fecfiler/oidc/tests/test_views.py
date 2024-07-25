from unittest.mock import Mock
from django.test import RequestFactory, TestCase
from django.contrib.auth import get_user_model

from fecfiler.oidc.views import (
    oidc_logout,
    login_redirect,
    logout_redirect,
)

UserModel = get_user_model()


class OidcTest(TestCase):
    fixtures = ["C01234567_user_and_committee"]
    user = None

    def setUp(self):
        self.user = UserModel.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
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

    def test_login_dot_gov_login_redirect(self):
        request = self.factory.get("/")
        request.user = self.user
        request.session = {}
        retval = login_redirect(request)
        self.assertEqual(retval.status_code, 302)

    def test_login_dot_gov_logout_redirect(self):
        retval = logout_redirect(self.factory.get("/"))
        self.assertEqual(retval.status_code, 302)
