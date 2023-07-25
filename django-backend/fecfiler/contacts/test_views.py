from unittest import mock

from django.test import RequestFactory, TestCase
from rest_framework.test import force_authenticate

from ..authentication.models import Account
from .models import Contact
from .views import ContactViewSet, DeletedContactsViewSet


def mocked_requests_get_candidates(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    return MockResponse(
        {
            "results": [
                {"name": "BIDEN, JOE R", "id": "P60012143", "office_sought": "P"},
                {
                    "name": "BIDEN, JR., JOSEPH R.",
                    "id": "P60012465",
                    "office_sought": "P",
                },
            ]
        },
        200,
    )


def mocked_requests_get_committees(*args, **kwargs):
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

    def test_candidate_lookup_no_auth(self):
        request = self.factory.get("/api/v1/contacts/candidate_lookup")

        response = ContactViewSet.as_view({"get": "candidate_lookup"})(request)

        self.assertEqual(response.status_code, 403)

    @mock.patch("requests.get", side_effect=mocked_requests_get_candidates)
    def test_candidate_lookup_no_q(self, mock_get):
        request = self.factory.get("/api/v1/contacts/candidate_lookup")
        request.user = self.user

        response = ContactViewSet.as_view({"get": "candidate_lookup"})(request)

        self.assertEqual(response.status_code, 400)

    @mock.patch("requests.get", side_effect=mocked_requests_get_candidates)
    def test_candidate_lookup_happy_path(self, mock_get):
        request = self.factory.get(
            "/api/v1/contacts/candidate_lookup?"
            "q=test&max_fecfile_results=5&max_fec_results=5"
        )
        request.user = self.user

        response = ContactViewSet.as_view({"get": "candidate_lookup"})(request)

        expected_json = {
            "fec_api_candidates": [
                {"name": "BIDEN, JOE R", "id": "P60012143", "office_sought": "P"},
                {
                    "name": "BIDEN, JR., JOSEPH R.",
                    "id": "P60012465",
                    "office_sought": "P",
                },
            ],
            "fecfile_candidates": [],
        }

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding="utf8"), expected_json)

    def test_committee_lookup_no_auth(self):
        request = self.factory.get("/api/v1/contacts/committee_lookup")

        response = ContactViewSet.as_view({"get": "committee_lookup"})(request)

        self.assertEqual(response.status_code, 403)

    @mock.patch("requests.get", side_effect=mocked_requests_get_committees)
    def test_committee_lookup_no_q(self, mock_get):
        request = self.factory.get("/api/v1/contacts/committee_lookup")
        request.user = self.user

        response = ContactViewSet.as_view({"get": "committee_lookup"})(request)

        self.assertEqual(response.status_code, 400)

    @mock.patch("requests.get", side_effect=mocked_requests_get_committees)
    def test_committee_lookup_happy_path(self, mock_get):
        request = self.factory.get(
            "/api/v1/contacts/committee_lookup?"
            "q=test&max_fecfile_results=5&max_fec_results=5"
        )
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

    def test_individual_lookup_no_q(self):
        request = self.factory.get("/api/v1/contacts/individual_lookup")
        request.user = self.user

        response = ContactViewSet.as_view({"get": "individual_lookup"})(request)

        self.assertEqual(response.status_code, 400)

    def test_individual_lookup_happy_path(self):
        request = self.factory.get(
            "/api/v1/contacts/individual_lookup?" "q=Lastname&max_fecfile_results=5"
        )
        request.user = self.user

        response = ContactViewSet.as_view({"get": "individual_lookup"})(request)

        expected_json_fragment = '"last_name": "Lastname", "first_name": ' '"Firstname"'

        self.assertEqual(response.status_code, 200)
        self.assertIn(expected_json_fragment, str(response.content, encoding="utf8"))

    def test_organization_lookup_no_q(self):
        request = self.factory.get("/api/v1/contacts/organization_lookup")
        request.user = self.user

        response = ContactViewSet.as_view({"get": "organization_lookup"})(request)

        self.assertEqual(response.status_code, 400)

    def test_organization_lookup_happy_path(self):
        request = self.factory.get(
            "/api/v1/contacts/organization_lookup?" "q=test&max_fecfile_results=5"
        )
        request.user = self.user

        response = ContactViewSet.as_view({"get": "organization_lookup"})(request)

        expected_json_fragment = '"name": "test name contains TestOrgName1"'

        self.assertEqual(response.status_code, 200)
        self.assertIn(expected_json_fragment, str(response.content, encoding="utf8"))

    def test_fec_id_is_unique_no_fec_id(self):
        request = self.factory.get("/api/v1/contacts/fec_id_is_unique")
        request.user = self.user

        response = ContactViewSet.as_view({"get": "fec_id_is_unique"})(request)

        self.assertEqual(response.status_code, 400)

    def test_fec_id_is_unique_happy_path(self):
        request = self.factory.get(
            "/api/v1/contacts/fec_id_is_unique?fec_id=test_fec_id"
            "&contact_id=a5061946-93ef-47f4-82f6-f1782c333d70"
        )
        request.user = self.user

        response = ContactViewSet.as_view({"get": "fec_id_is_unique"})(request)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data)

    def test_restore_no_match(self):
        request = self.factory.post(
            "/api/v1/contacts-deleted/restore",
            ["a5061946-0000-0000-82f6-f1782c333d70"],
            "application/json",
        )
        force_authenticate(request, self.user)
        response = DeletedContactsViewSet.as_view({"post": "restore"})(request)
        self.assertEqual(response.status_code, 400)

    def test_restore(self):
        contact = Contact.objects.create(
            id="a5061946-0000-0000-82f6-f1782c333d70",
            type=Contact.ContactType.INDIVIDUAL,
            last_name="Last",
            first_name="First",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
        )
        contact.delete()
        deleted_contact = Contact.all_objects.get(
            id="a5061946-0000-0000-82f6-f1782c333d70"
        )
        self.assertIsNotNone(deleted_contact.deleted)
        request = self.factory.post(
            "/api/v1/contacts-deleted/restore",
            ["a5061946-0000-0000-82f6-f1782c333d70"],
            "application/json",
        )
        force_authenticate(request, self.user)
        response = DeletedContactsViewSet.as_view({"post": "restore"})(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, ["a5061946-0000-0000-82f6-f1782c333d70"])
