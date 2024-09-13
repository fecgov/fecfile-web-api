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
    test_kid,
    test_username,
    test_email,
)


class OidcTest(TestCase):
    fixtures = ["fixtures/e2e-test-data"]

    def setUp(self):
        self.factory = RequestFactory()

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

    def test_certs_happy_path(self):
        request = self.factory.get("/")
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
        self.assertEqual(key_dict.get("kid"), test_kid)

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
        test_nonce = "test_nonce"
        test_access_token = "test_access_token"
        test_auth_data = {
            "nonce": test_nonce,
            "access_token": test_access_token,
        }
        test_payload = {"code": test_code}
        expected_content = "call to authorize endpoint is required first"

        mock_redis_get.side_effect = lambda _: json.dumps(test_auth_data).encode()

        request = self.factory.post("/", test_payload)
        retval = token(request)

        self.assertEqual(retval.status_code, 400)
        self.assertEqual(expected_content, retval.content.decode())

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.get")
    def test_token_authorize_code_invalid(self, mock_redis_get):
        test_code = "test_code"
        test_nonce = "test_nonce"
        test_access_token = "test_access_token"
        test_auth_data = {
            "code": test_code,
            "nonce": test_nonce,
            "access_token": test_access_token,
        }
        mismatched_test_code = "mismatched_test_code"
        test_payload = {"code": mismatched_test_code}
        expected_content = "authorize code is invalid"

        mock_redis_get.side_effect = lambda _: json.dumps(test_auth_data).encode()

        request = self.factory.post("/", test_payload)
        retval = token(request)

        self.assertEqual(retval.status_code, 400)
        self.assertEqual(expected_content, retval.content.decode())

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.get")
    def test_token_happy_path(self, mock_redis_get):
        test_code = "test_code"
        test_nonce = "test_nonce"
        test_access_token = "test_access_token"
        test_auth_data = {
            "code": test_code,
            "nonce": test_nonce,
            "access_token": test_access_token,
        }
        test_payload = {"code": test_code}

        mock_redis_get.side_effect = lambda _: json.dumps(test_auth_data).encode()

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
    def test_userinfo_no_auth_header(self, mock_redis_get):
        test_code = "test_code"
        test_nonce = "test_nonce"
        test_access_token = "test_access_token"
        test_auth_data = {
            "code": test_code,
            "nonce": test_nonce,
            "access_token": test_access_token,
        }
        expected_contents = "Authorization header is required"

        mock_redis_get.side_effect = lambda _: json.dumps(test_auth_data).encode()

        request = self.factory.get("/")
        retval = userinfo(request)
        actual_contents = retval.content.decode()

        self.assertEqual(retval.status_code, 400)
        self.assertEqual(expected_contents, actual_contents)

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.get")
    def test_userinfo_no_auth_data_access_token(self, mock_redis_get):
        test_code = "test_code"
        test_nonce = "test_nonce"
        test_access_token = "test_access_token"
        test_auth_data = {
            "code": test_code,
            "nonce": test_nonce,
        }
        test_headers = {"Authorization": f"Bearer {test_access_token}"}
        expected_contents = "call to authorize endpoint is required first"

        mock_redis_get.side_effect = lambda _: json.dumps(test_auth_data).encode()

        request = self.factory.get("/", headers=test_headers)
        retval = userinfo(request)
        actual_contents = retval.content.decode()

        self.assertEqual(retval.status_code, 400)
        self.assertEqual(expected_contents, actual_contents)

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.get")
    def test_userinfo_bearer_token_not_found(self, mock_redis_get):
        test_code = "test_code"
        test_nonce = "test_nonce"
        test_access_token = "test_access_token"
        test_auth_data = {
            "code": test_code,
            "nonce": test_nonce,
            "access_token": test_access_token,
        }
        test_headers = {"Authorization": f"{test_access_token}"}
        expected_contents = "Bearer token not found"

        mock_redis_get.side_effect = lambda _: json.dumps(test_auth_data).encode()

        request = self.factory.get("/", headers=test_headers)
        retval = userinfo(request)
        actual_contents = retval.content.decode()

        self.assertEqual(retval.status_code, 400)
        self.assertEqual(expected_contents, actual_contents)

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.get")
    def test_userinfo_bearer_token_invalid(self, mock_redis_get):
        test_code = "test_code"
        test_nonce = "test_nonce"
        test_access_token = "test_access_token"
        test_auth_data = {
            "code": test_code,
            "nonce": test_nonce,
            "access_token": test_access_token,
        }
        test_invalid_bearer_token = "test_invalid_bearer_token"
        test_headers = {"Authorization": f"Bearer {test_invalid_bearer_token}"}
        expected_contents = "Invalid Bearer token"

        mock_redis_get.side_effect = lambda _: json.dumps(test_auth_data).encode()

        request = self.factory.get("/", headers=test_headers)
        retval = userinfo(request)
        actual_contents = retval.content.decode()

        self.assertEqual(retval.status_code, 400)
        self.assertEqual(expected_contents, actual_contents)

    @patch("fecfiler.mock_oidc_provider.views.redis.Redis.get")
    def test_userinfo_happy_path(self, mock_redis_get):
        test_code = "test_code"
        test_nonce = "test_nonce"
        test_access_token = "test_access_token"
        test_auth_data = {
            "code": test_code,
            "nonce": test_nonce,
            "access_token": test_access_token,
        }
        test_headers = {"Authorization": f"Bearer {test_access_token}"}
        expected_contents = json.dumps(
            {
                "sub": test_username,
                "email": test_email,
            }
        )

        mock_redis_get.side_effect = lambda _: json.dumps(test_auth_data).encode()

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
