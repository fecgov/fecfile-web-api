from unittest.mock import patch
from django.test import RequestFactory, TestCase
import json

from fecfiler.mock_oidc_provider.views import (
    discovery,
    certs,
    authorize,
    token,
    userinfo,
    logout,
    MOCK_OIDC_PROVIDER_DATA,
    MOCK_OIDC_PROVIDER_KDAT,
    MOCK_OIDC_PROVIDER_USER_IDX,
    users,
)


class OidcTest(TestCase):
    fixtures = ["fixtures/user-data"]

    def setUp(self):
        self.factory = RequestFactory()
        self.test_auth_data = {
            "code": "test_code",
            "nonce": "test_nonce",
            "access_token": "test_access_token",
        }

    # discovery

    @patch("fecfiler.mock_oidc_provider.views.reverse")
    def test_discovery_happy_path(self, reverse_mock):
        reverse_mock.side_effect = lambda x: f"/oidc_provider/{x}"
        expected_content = json.dumps(
            {
                "authorization_endpoint": "http://testserver/oidc_provider/authorize",
                "issuer": "http:testserver",
                "jwks_uri": "http://testserver/oidc_provider/certs",
                "token_endpoint": "http://testserver/oidc_provider/token",
                "userinfo_endpoint": "http://testserver/oidc_provider/userinfo",
                "end_session_endpoint": "http://testserver/oidc_provider/logout",
            }
        )
        request = self.factory.get("/")
        retval = discovery(request)
        actual_content = retval.content.decode()

        self.assertEqual(retval.status_code, 200)
        self.assertEqual(expected_content, actual_content)

    # certs

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.get")
    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.set")
    def test_certs_happy_path(self, mock_redis_set, mock_redis_get):
        request = self.factory.get("/")

        mock_redis_get.side_effect = lambda _: None

        retval = certs(request)
        actual_json_content = json.loads(retval.content)
        key_dict = actual_json_content.get("keys")[0]

        self.assertEqual(retval.status_code, 200)
        self.assertTrue("keys" in actual_json_content)
        self.assertEqual(key_dict.get("alg"), "RS256")
        self.assertEqual(key_dict.get("use"), "sig")
        self.assertEqual(key_dict.get("kty"), "RSA")
        self.assertTrue("n" in key_dict)
        self.assertEqual(key_dict.get("e"), "AQAB")
        self.assertIsNotNone(key_dict.get("kid"))

    # authorize

    def test_authorize_missing_redirect_uri(self):
        test_state = "test_state"
        test_nonce = "test_nonce"
        expected_content = "redirect_uri, state, nonce query params are required"

        request = self.factory.get(f"/?state={test_state}&nonce={test_nonce}")
        retval = authorize(request)

        self.assertEqual(retval.status_code, 400)
        self.assertEqual(expected_content, retval.content.decode())

    def test_authorize_missing_state(self):
        test_redirect_uri = "test_redirect_uri"
        test_nonce = "test_nonce"
        expected_content = "redirect_uri, state, nonce query params are required"

        request = self.factory.get(
            f"/?redirect_uri={test_redirect_uri}&nonce={test_nonce}"
        )
        retval = authorize(request)

        self.assertEqual(retval.status_code, 400)
        self.assertEqual(expected_content, retval.content.decode())

    def test_authorize_missing_nonce(self):
        test_redirect_uri = "test_redirect_uri"
        test_state = "test_state"
        expected_content = "redirect_uri, state, nonce query params are required"

        request = self.factory.get(
            f"/?redirect_uri={test_redirect_uri}&state={test_state}"
        )
        retval = authorize(request)

        self.assertEqual(retval.status_code, 400)
        self.assertEqual(expected_content, retval.content.decode())

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.set")
    def test_authorize_happy_path(self, mock_redis_set):
        test_redirect_uri = "test_redirect_uri"
        test_state = "test_state"
        test_nonce = "test_nonce"

        request = self.factory.get(
            f"/?redirect_uri={test_redirect_uri}&state={test_state}&nonce={test_nonce}"
        )
        retval = authorize(request)
        redirect_url = retval.url

        self.assertEqual(retval.status_code, 302)
        self.assertTrue(redirect_url.startswith(f"{test_redirect_uri}?"))
        self.assertTrue(f"&state={test_state}" in redirect_url)

    # token

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.get")
    def test_token_no_auth_data_code(self, mock_redis_get):
        test_code = "test_code"
        test_payload = {"code": test_code}
        expected_content = "call to authorize endpoint is required first"

        self.test_auth_data = {
            "nonce": "test_nonce",
            "access_token": "test_access_token",
        }
        mock_redis_get.side_effect = self.redis_get_mock

        request = self.factory.post("/", test_payload)
        retval = token(request)

        self.assertEqual(retval.status_code, 400)
        self.assertEqual(expected_content, retval.content.decode())

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.get")
    def test_token_authorize_code_invalid(self, mock_redis_get):
        mismatched_test_code = "mismatched_test_code"
        test_payload = {"code": mismatched_test_code}
        expected_content = "authorize code is invalid"

        mock_redis_get.side_effect = self.redis_get_mock

        request = self.factory.post("/", test_payload)
        retval = token(request)

        self.assertEqual(retval.status_code, 400)
        self.assertEqual(expected_content, retval.content.decode())

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.get")
    @patch("fecfiler.mock_oidc_provider.views.jwt.encode")
    def test_token_happy_path(self, mock_jwt_encode, mock_redis_get):
        test_code = "test_code"
        test_access_token = "test_access_token"
        test_payload = {"code": test_code}

        mock_redis_get.side_effect = self.redis_get_mock
        mock_jwt_encode.side_effect = lambda *args, **kwargs: "test_jwt_encoded"

        request = self.factory.post("/", test_payload)
        retval = token(request)
        actual_json_content = json.loads(retval.content)

        self.assertEqual(retval.status_code, 200)
        self.assertEqual(actual_json_content.get("access_token"), test_access_token)
        self.assertEqual(actual_json_content.get("token_type"), "Bearer")
        self.assertEqual(actual_json_content.get("expires_in"), 3600)
        self.assertTrue("id_token" in actual_json_content)

    # userinfo

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.get")
    def test_userinfo_happy_path(self, mock_redis_get):
        test_access_token = "test_access_token"
        test_headers = {"Authorization": f"Bearer {test_access_token}"}
        expected_contents = json.dumps(
            {
                "sub": users[0]["username"],
                "email": users[0]["email"],
            }
        )

        mock_redis_get.side_effect = self.redis_get_mock

        request = self.factory.get("/", headers=test_headers)
        retval = userinfo(request)
        actual_contents = retval.content.decode()

        self.assertEqual(retval.status_code, 200)
        self.assertEqual(expected_contents, actual_contents)

    # logout

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.delete")
    def test_logout_no_post_logout_redirect_uri(self, mock_redis_delete):
        test_state = "test_state"
        expected_content = "post_logout_redirect_uri param is required"

        request = self.factory.get(f"/?state={test_state}")
        retval = logout(request)

        self.assertEqual(retval.status_code, 400)
        self.assertEqual(retval.content.decode(), expected_content)

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.delete")
    def test_logout_happy_path(self, mock_redis_delete):
        test_logout_redirect_uri = "test_logout_redirect_uri"
        test_state = "test_state"
        expected_redirect_url = f"{test_logout_redirect_uri}?state={test_state}"

        request = self.factory.get(
            f"/?post_logout_redirect_uri={test_logout_redirect_uri}&state={test_state}"
        )
        retval = logout(request)

        self.assertEqual(retval.status_code, 302)
        self.assertEqual(retval.url, expected_redirect_url)

    def redis_get_mock(self, key):
        if key == MOCK_OIDC_PROVIDER_DATA:
            return json.dumps(self.test_auth_data).encode()
        elif key == MOCK_OIDC_PROVIDER_KDAT:
            return json.dumps(
                {
                    "kid": "test_kid",
                    "pubkey": "test_pubkey",
                    "pvtkey": "test_pvtkey",
                }
            )
        elif key == MOCK_OIDC_PROVIDER_USER_IDX:
            return 0
        return None
