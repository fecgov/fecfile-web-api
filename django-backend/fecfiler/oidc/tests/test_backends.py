from unittest.mock import Mock, patch
from requests.exceptions import HTTPError
from django.core.exceptions import SuspiciousOperation
from django.test import RequestFactory, TestCase
from fecfiler.oidc.backends import OIDCAuthenticationBackend


class OIDCAuthenticationBackendTestCase(TestCase):
    def setUp(self):
        self.backend = OIDCAuthenticationBackend()

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwt")
    def test_authenticate_bad_token_response(
        self,
        jwt_mock,
        requests_mock,
    ):
        post_json_mock = Mock(status_code=500)
        requests_mock.post.return_value = post_json_mock

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        with self.assertRaises(HTTPError):
            self.backend.authenticate(request=auth_request)

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwk")
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.jws")
    def test_authenticate_nonce_verification_failed(
        self,
        jws_mock,
        jwt_mock,
        jwk_mock,
        requests_mock,
    ):
        test_jws_payload = b'{"nonce": "test_nonce_value"}'

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }

        get_json_mock = Mock(status_code=200)

        requests_mock.post.return_value = post_json_mock
        requests_mock.get.return_value = get_json_mock
        jws_mock.JWS.return_value.payload = test_jws_payload

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        with self.assertRaisesMessage(
            SuspiciousOperation,
            "JWT Nonce verification failed.",
        ):
            self.backend.authenticate(
                request=auth_request, nonce="test_nonce_value_mismatched"
            )

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwk")
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.jws")
    def test_authenticate_payload_claims_verification_failed(
        self,
        jws_mock,
        jwt_mock,
        jwk_mock,
        requests_mock,
    ):
        test_jws_payload = b'{"nonce": "test_nonce_value"}'

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }

        get_json_mock = Mock(status_code=200)
        get_json_mock.json.side_effect = [
            {"username": "test_username"},
        ]

        requests_mock.post.return_value = post_json_mock
        requests_mock.get.return_value = get_json_mock
        jws_mock.JWS.return_value.payload = test_jws_payload

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        with self.assertRaisesMessage(
            SuspiciousOperation,
            "Claims verification failed",
        ):
            self.backend.authenticate(request=auth_request, nonce="test_nonce_value")

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwk")
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.jws")
    @patch("fecfiler.oidc.backends.len")
    def test_authenticate_oidc_op_unique_identifier_not_found(
        self,
        len_mock,
        jws_mock,
        jwt_mock,
        jwk_mock,
        requests_mock,
    ):
        test_jws_payload = b'{"nonce": "test_nonce_value"}'

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }

        get_json_mock = Mock(status_code=200)
        get_json_mock.json.side_effect = [
            {"email": "test_email", "username": "test_username"},
        ]

        requests_mock.post.return_value = post_json_mock
        requests_mock.get.return_value = get_json_mock
        jws_mock.JWS.return_value.payload = test_jws_payload
        len_mock.return_value = 2

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        with self.assertRaisesMessage(
            SuspiciousOperation,
            "Failed to retrieve OIDC_OP_UNIQUE_IDENTIFIER sub from claims",
        ):
            self.backend.authenticate(request=auth_request, nonce="test_nonce_value")

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwk")
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.jws")
    @patch("fecfiler.oidc.backends.len")
    def test_authenticate_payload_multiple_users_returned(
        self,
        len_mock,
        jws_mock,
        jwt_mock,
        jwk_mock,
        requests_mock,
    ):
        test_jws_payload = b'{"nonce": "test_nonce_value"}'

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }

        get_json_mock = Mock(status_code=200)
        get_json_mock.json.side_effect = [
            {"sub": "test_sub", "email": "test_email", "username": "test_username"},
        ]

        requests_mock.post.return_value = post_json_mock
        requests_mock.get.return_value = get_json_mock
        jws_mock.JWS.return_value.payload = test_jws_payload
        len_mock.return_value = 2

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        with self.assertRaisesMessage(
            SuspiciousOperation,
            "Multiple users returned",
        ):
            self.backend.authenticate(request=auth_request, nonce="test_nonce_value")

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwk")
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.jws")
    @patch("fecfiler.oidc.backends.len")
    def test_authenticate_payload_create_new_user_happy_path(
        self,
        len_mock,
        jws_mock,
        jwt_mock,
        jwk_mock,
        requests_mock,
    ):
        test_jws_payload = b'{"nonce": "test_nonce_value"}'

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }

        get_json_mock = Mock(status_code=200)
        get_json_mock.json.side_effect = [
            {"sub": "test_sub", "email": "test_email", "username": "test_username"},
        ]

        requests_mock.post.return_value = post_json_mock
        requests_mock.get.return_value = get_json_mock
        jws_mock.JWS.return_value.payload = test_jws_payload
        len_mock.return_value = 0

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})

        self.backend.UserModel.objects.create_user = Mock()
        retval = self.backend.authenticate(request=auth_request, nonce="test_nonce_value")
        self.assertIsNotNone(retval)
