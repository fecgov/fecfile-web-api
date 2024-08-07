"""
This source code has been copied from the mozilla-django-oidc
project:
https://mozilla-django-oidc.readthedocs.io/en/stable/index.html#
https://github.com/mozilla/mozilla-django-oidc/tree/main

It has been modified in places to meet the needs of the project and
the original version can be found on Github:
https://github.com/mozilla/mozilla-django-oidc/blob/main/tests/test_auth.py
"""

from unittest.mock import Mock, patch
from requests.exceptions import HTTPError
from django.core.exceptions import SuspiciousOperation
from django.test import RequestFactory, TestCase, override_settings
from fecfiler.oidc.backends import OIDCAuthenticationBackend


@override_settings(OIDC_OP_TOKEN_ENDPOINT="https://server.example.com/token")
@override_settings(OIDC_OP_USER_ENDPOINT="https://server.example.com/user")
@override_settings(OIDC_RP_CLIENT_ID="example_id")
@override_settings(OIDC_RP_CLIENT_SECRET="client_secret")
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
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.JWS")
    def test_authenticate_invalid_jwks(
        self,
        jws_mock,
        jwt_mock,
        requests_mock,
    ):
        test_jws_json_header = '{"kid":"test_kid","alg":"RS256"}'

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }
        requests_mock.post.return_value = post_json_mock
        jws_mock.from_compact.return_value.signature.protected = test_jws_json_header

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        with self.assertRaisesMessage(
            SuspiciousOperation, "Could not find a valid JWKS."
        ):
            self.backend.authenticate(request=auth_request)

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.JWS")
    def test_authenticate_verify_jws_failed_no_alg(
        self,
        jws_mock,
        jwt_mock,
        requests_mock,
    ):
        test_jws_json_header = '{"kid":"test_kid","alg":"RS256"}'
        test_jwks = {"keys": [{"alg": "RS256", "kid": "test_kid"}]}

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }

        get_json_mock = Mock(status_code=200)
        get_json_mock.json.return_value = test_jwks

        requests_mock.post.return_value = post_json_mock
        requests_mock.get.return_value = get_json_mock
        jws_mock.from_compact.return_value.signature.protected = test_jws_json_header
        jws_mock.from_compact.return_value.signature.combined = {}

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        with self.assertRaisesMessage(
            SuspiciousOperation, "No alg value found in header"
        ):
            self.backend.authenticate(request=auth_request)

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.JWS")
    def test_authenticate_verify_jws_failed_alg_does_not_match(
        self,
        jws_mock,
        jwt_mock,
        requests_mock,
    ):
        test_jws_json_header = '{"kid":"test_kid","alg":"RS256"}'
        test_jwks = {"keys": [{"alg": "RS256", "kid": "test_kid"}]}
        test_alg = "invalid_alg_name"

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }

        get_json_mock = Mock(status_code=200)
        get_json_mock.json.return_value = test_jwks

        requests_mock.post.return_value = post_json_mock
        requests_mock.get.return_value = get_json_mock
        jws_mock.from_compact.return_value.signature.protected = test_jws_json_header
        jws_mock.from_compact.return_value.signature.combined.alg.name = test_alg

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        with self.assertRaisesMessage(
            SuspiciousOperation,
            "The provider algorithm {!r} does not match the client's "
            "OIDC_RP_SIGN_ALGO.".format("invalid_alg_name"),
        ):
            self.backend.authenticate(request=auth_request)

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.JWS")
    def test_authenticate_verify_jws_lib_call_failed(
        self,
        jws_mock,
        jwt_mock,
        requests_mock,
    ):
        test_jws_json_header = '{"kid":"test_kid","alg":"RS256"}'
        test_jwks = {
            "keys": [
                {
                    "alg": "RS256",
                    "use": "sig",
                    "kty": "RSA",
                    "n": "test_n",
                    "e": "test_e",
                    "kid": "test_kid",
                }
            ]
        }
        test_alg = "RS256"

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }

        get_json_mock = Mock(status_code=200)
        get_json_mock.json.return_value = test_jwks

        requests_mock.post.return_value = post_json_mock
        requests_mock.get.return_value = get_json_mock
        jws_mock.from_compact.return_value.signature.protected = test_jws_json_header
        jws_mock.from_compact.return_value.signature.combined.alg.name = test_alg
        jws_mock.from_compact.return_value.verify.return_value = False

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        with self.assertRaisesMessage(
            SuspiciousOperation,
            "JWS token verification failed",
        ):
            self.backend.authenticate(request=auth_request)

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.JWS")
    def test_authenticate_nonce_verification_failed(
        self,
        jws_mock,
        jwt_mock,
        requests_mock,
    ):
        test_jws_json_header = '{"kid":"test_kid","alg":"RS256"}'
        test_jwks = {
            "keys": [
                {
                    "alg": "RS256",
                    "use": "sig",
                    "kty": "RSA",
                    "n": "test_n",
                    "e": "test_e",
                    "kid": "test_kid",
                }
            ]
        }
        test_alg = "RS256"
        test_jws_payload = b'{"nonce": "test_nonce_value"}'

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }

        get_json_mock = Mock(status_code=200)
        get_json_mock.json.return_value = test_jwks

        requests_mock.post.return_value = post_json_mock
        requests_mock.get.return_value = get_json_mock
        jws_mock.from_compact.return_value.signature.protected = test_jws_json_header
        jws_mock.from_compact.return_value.signature.combined.alg.name = test_alg
        jws_mock.from_compact.return_value.verify.return_value = True
        jws_mock.from_compact.return_value.payload = test_jws_payload

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        with self.assertRaisesMessage(
            SuspiciousOperation,
            "JWT Nonce verification failed.",
        ):
            self.backend.authenticate(
                request=auth_request, nonce="test_nonce_value_mismatched"
            )

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.JWS")
    def test_authenticate_payload_claims_verification_failed(
        self,
        jws_mock,
        jwt_mock,
        requests_mock,
    ):
        test_jws_json_header = '{"kid":"test_kid","alg":"RS256"}'
        test_jwks = {
            "keys": [
                {
                    "alg": "RS256",
                    "use": "sig",
                    "kty": "RSA",
                    "n": "test_n",
                    "e": "test_e",
                    "kid": "test_kid",
                }
            ]
        }
        test_alg = "RS256"
        test_jws_payload = b'{"nonce": "test_nonce_value"}'

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }

        get_json_mock = Mock(status_code=200)
        get_json_mock.json.return_value = test_jwks

        requests_mock.post.return_value = post_json_mock
        requests_mock.get.return_value = get_json_mock
        jws_mock.from_compact.return_value.signature.protected = test_jws_json_header
        jws_mock.from_compact.return_value.signature.combined.alg.name = test_alg
        jws_mock.from_compact.return_value.verify.return_value = True
        jws_mock.from_compact.return_value.payload = test_jws_payload

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        with self.assertRaisesMessage(
            SuspiciousOperation,
            "Claims verification failed",
        ):
            self.backend.authenticate(request=auth_request, nonce="test_nonce_value")

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.JWS")
    @patch("fecfiler.oidc.backends.len")
    def test_authenticate_oidc_op_unique_identifier_not_found(
        self,
        len_mock,
        jws_mock,
        jwt_mock,
        requests_mock,
    ):
        test_jws_json_header = '{"kid":"test_kid","alg":"RS256"}'
        test_jwks = {
            "keys": [
                {
                    "alg": "RS256",
                    "use": "sig",
                    "kty": "RSA",
                    "n": "test_n",
                    "e": "test_e",
                    "kid": "test_kid",
                }
            ]
        }
        test_alg = "RS256"
        test_jws_payload = b'{"nonce": "test_nonce_value"}'

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }

        get_json_mock = Mock(status_code=200)
        get_json_mock.json.side_effect = [
            test_jwks,
            {"email": "test_email", "username": "test_username"},
        ]

        requests_mock.post.return_value = post_json_mock
        requests_mock.get.return_value = get_json_mock
        jws_mock.from_compact.return_value.signature.protected = test_jws_json_header
        jws_mock.from_compact.return_value.signature.combined.alg.name = test_alg
        jws_mock.from_compact.return_value.verify.return_value = True
        jws_mock.from_compact.return_value.payload = test_jws_payload
        len_mock.return_value = 2

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        with self.assertRaisesMessage(
            SuspiciousOperation,
            "Failed to retrieve OIDC_OP_UNIQUE_IDENTIFIER sub from claims",
        ):
            self.backend.authenticate(request=auth_request, nonce="test_nonce_value")

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.JWS")
    @patch("fecfiler.oidc.backends.len")
    def test_authenticate_payload_multiple_users_returned(
        self,
        len_mock,
        jws_mock,
        jwt_mock,
        requests_mock,
    ):
        test_jws_json_header = '{"kid":"test_kid","alg":"RS256"}'
        test_jwks = {
            "keys": [
                {
                    "alg": "RS256",
                    "use": "sig",
                    "kty": "RSA",
                    "n": "test_n",
                    "e": "test_e",
                    "kid": "test_kid",
                }
            ]
        }
        test_alg = "RS256"
        test_jws_payload = b'{"nonce": "test_nonce_value"}'

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }

        get_json_mock = Mock(status_code=200)
        get_json_mock.json.side_effect = [
            test_jwks,
            {"sub": "test_sub", "email": "test_email", "username": "test_username"},
        ]

        requests_mock.post.return_value = post_json_mock
        requests_mock.get.return_value = get_json_mock
        jws_mock.from_compact.return_value.signature.protected = test_jws_json_header
        jws_mock.from_compact.return_value.signature.combined.alg.name = test_alg
        jws_mock.from_compact.return_value.verify.return_value = True
        jws_mock.from_compact.return_value.payload = test_jws_payload
        len_mock.return_value = 2

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})
        with self.assertRaisesMessage(
            SuspiciousOperation,
            "Multiple users returned",
        ):
            self.backend.authenticate(request=auth_request, nonce="test_nonce_value")

    @patch("fecfiler.oidc.backends.requests")
    @patch("fecfiler.oidc.backends.jwt")
    @patch("fecfiler.oidc.backends.JWS")
    @patch("fecfiler.oidc.backends.len")
    def test_authenticate_payload_create_new_user_happy_path(
        self,
        len_mock,
        jws_mock,
        jwt_mock,
        requests_mock,
    ):
        test_jws_json_header = '{"kid":"test_kid","alg":"RS256"}'
        test_jwks = {
            "keys": [
                {
                    "alg": "RS256",
                    "use": "sig",
                    "kty": "RSA",
                    "n": "test_n",
                    "e": "test_e",
                    "kid": "test_kid",
                }
            ]
        }
        test_alg = "RS256"
        test_jws_payload = b'{"nonce": "test_nonce_value"}'

        post_json_mock = Mock(status_code=200)
        post_json_mock.json.return_value = {
            "id_token": "id_token",
            "access_token": "access_granted",
        }

        get_json_mock = Mock(status_code=200)
        get_json_mock.json.side_effect = [
            test_jwks,
            {"sub": "test_sub", "email": "test_email", "username": "test_username"},
        ]

        requests_mock.post.return_value = post_json_mock
        requests_mock.get.return_value = get_json_mock
        jws_mock.from_compact.return_value.signature.protected = test_jws_json_header
        jws_mock.from_compact.return_value.signature.combined.alg.name = test_alg
        jws_mock.from_compact.return_value.verify.return_value = True
        jws_mock.from_compact.return_value.payload = test_jws_payload
        len_mock.return_value = 0

        auth_request = RequestFactory().get("/foo", {"code": "foo", "state": "bar"})

        self.backend.UserModel.objects.create_user = Mock()
        retval = self.backend.authenticate(request=auth_request, nonce="test_nonce_value")
        self.assertIsNotNone(retval)
