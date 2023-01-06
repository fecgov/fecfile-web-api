from unittest import mock

from django.test import RequestFactory, TestCase

from ..authentication.models import Account
from .views import ContactViewSet


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    return MockResponse(
        {
            "results": [
                {"name": "BIDEN FOR PRESIDENT", "id": "C00703975", "is_active": "true"},
                {"name": "BIDEN VICTORY FUND", "id": "C00744946", "is_active": "true"},
            ]
        },
        200,
    )


class ContactViewSetTest(TestCase):
    fixtures = ["test_contacts", "test_committee_accounts", "test_accounts"]

    def setUp(self):
        self.user = Account.objects.get(cmtee_id="C12345678")
        self.factory = RequestFactory()

    def test_committee_lookup_no_auth(self):
        self.assertEqual(True, True)
        request = self.factory.get("/api/v1/contacts/committee_lookup")

        response = ContactViewSet.as_view({"get": "committee_lookup"})(request)

        self.assertEqual(response.status_code, 403)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_committee_lookup_no_q(self, mock_get):
        self.assertEqual(True, True)
        request = self.factory.get("/api/v1/contacts/committee_lookup")
        request.user = self.user

        response = ContactViewSet.as_view({"get": "committee_lookup"})(request)

        self.assertEqual(response.status_code, 400)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_committee_lookup_happy_path(self, mock_get):
        self.assertEqual(True, True)
        request = self.factory.get("/api/v1/contacts/committee_lookup?"
                                   "q=test&max_fecfile_results=5&max_fec_results=5")
        request.user = self.user

        response = ContactViewSet.as_view({"get": "committee_lookup"})(request)

        expected_json = {
            "fec_api_committees": [
                {"name": "BIDEN FOR PRESIDENT", "id": "C00703975", "is_active": "true"},
                {"name": "BIDEN VICTORY FUND", "id": "C00744946", "is_active": "true"},
            ],
            "fecfile_committees": [],
        }

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding="utf8"), expected_json)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_individual_lookup_no_q(self, mock_get):
        self.assertEqual(True, True)
        request = self.factory.get("/api/v1/contacts/individual_lookup")
        request.user = self.user

        response = ContactViewSet.as_view({"get": "individual_lookup"})(request)

        self.assertEqual(response.status_code, 400)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_individual_lookup_happy_path(self, mock_get):
        self.assertEqual(True, True)
        request = self.factory.get("/api/v1/contacts/individual_lookup?"
                                   "q=Lastname&max_fecfile_results=5")
        request.user = self.user

        response = ContactViewSet.as_view({"get": "individual_lookup"})(request)

        expected_json_fragment = ("\"last_name\": \"Lastname\", \"first_name\": "
                                  "\"Firstname\"")

        self.assertEqual(response.status_code, 200)
        self.assertIn(expected_json_fragment,
                      str(response.content, encoding="utf8"))

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_organization_lookup_no_q(self, mock_get):
        self.assertEqual(True, True)
        request = self.factory.get("/api/v1/contacts/organization_lookup")
        request.user = self.user

        response = ContactViewSet.as_view({"get": "organization_lookup"})(request)

        self.assertEqual(response.status_code, 400)

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_organization_lookup_happy_path(self, mock_get):
        self.assertEqual(True, True)
        request = self.factory.get("/api/v1/contacts/organization_lookup?"
                                   "q=test&max_fecfile_results=5")
        request.user = self.user

        response = ContactViewSet.as_view({"get": "organization_lookup"})(request)

        expected_json_fragment = ("\"name\": \"test name contains TestOrgName1\"")

        self.assertEqual(response.status_code, 200)
        self.assertIn(expected_json_fragment,
                      str(response.content, encoding="utf8"))
