from django.test import TestCase, RequestFactory
from .views import ContactViewSet
from ..authentication.models import Account
from unittest import mock


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    return MockResponse({"results": [
        {
            "name": "BIDEN FOR PRESIDENT",
            "id": "C00703975",
            "is_active": "true"
        },
        {
            "name": "BIDEN VICTORY FUND",
            "id": "C00744946",
            "is_active": "true"
        }
    ]}, 200)


class ContactViewSetTest(TestCase):
    fixtures = ["test_contacts", "test_committee_accounts", "test_accounts"]

    def setUp(self):
        self.user = Account.objects.get(cmtee_id="C12345678")
        self.factory = RequestFactory()

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_committee_lookup_happy_path(self, mock_get):
        self.assertEqual(True, True)
        request = self.factory.get("/api/v1/contacts/committee_lookup")
        request.user = self.user

        response = ContactViewSet.as_view({"get": "committee_lookup"})(request)

        expected_json = {
            "fec_api_cmtees": [
                {
                    "name": "BIDEN FOR PRESIDENT",
                    "id": "C00703975",
                    "is_active": "true"
                },
                {
                    "name": "BIDEN VICTORY FUND",
                    "id": "C00744946",
                    "is_active": "true"
                }
            ],
            "fecfile_cmtees": []
        }

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content,
                             encoding="utf8"), expected_json)
