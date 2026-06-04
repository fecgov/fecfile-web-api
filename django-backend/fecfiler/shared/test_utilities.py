from django.test import TestCase
from .utilities import generate_fec_uid, get_float_from_string, get_boolean_from_string
from urllib.parse import urlparse


class SharedUtilitiesTestCase(TestCase):
    def test_uid_has_length_20(self):
        uid = generate_fec_uid()
        self.assertEqual(len(uid), 20)

    def test_uid_all_uppercase(self):
        uid = generate_fec_uid()
        upper = uid.upper()
        self.assertEqual(uid, upper)

    def test_get_fallback_from_invalid_string(self):
        value = get_float_from_string("Invalid Error", 20.2)
        self.assertEqual(value, 20.2)

    def test_get_float_from_good_string(self):
        value = get_float_from_string("10.05", 1)
        self.assertEqual(value, 10.05)

    def test_get_fallback_from_none_string(self):
        value = get_float_from_string(None, 1)
        self.assertEqual(value, 1)

    def test_get_boolean_from_true_string(self):
        value = get_boolean_from_string("true")
        self.assertTrue(value)
        value = get_boolean_from_string("True")
        self.assertTrue(value)

    def test_get_boolean_from_false_string(self):
        value = get_boolean_from_string("false")
        self.assertFalse(value)
        value = get_boolean_from_string("Frue")
        self.assertFalse(value)
        value = get_boolean_from_string("")
        self.assertFalse(value)


def login_testcase_client(client):
    client.request_name = "_log_in"
    authenticate_response = client.get(
        "/api/v1/oidc/authenticate", allow_redirects=False
    )
    authenticate_redirect_uri = get_redirect_uri_from_redirect_response(
        authenticate_response)
    authorize_response = client.get(
        authenticate_redirect_uri,
        allow_redirects=False,
    )
    authorize_redirect_uri = get_redirect_uri_from_redirect_response(authorize_response)
    client.get(authorize_redirect_uri, allow_redirects=False)
    if not client.headers:
        client.headers = {}
    client.headers["x-csrftoken"] = client.cookies["csrftoken"]


def get_redirect_uri_from_redirect_response(response):
    if response.status_code == 302:
        parsed_url = urlparse(response.headers["Location"])
        return f"{parsed_url.path}?{parsed_url.query}"
    return None
