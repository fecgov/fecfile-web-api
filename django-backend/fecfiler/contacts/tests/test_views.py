import json
from unittest.mock import patch, Mock
import uuid

from ..models import Contact
from ..views import ContactViewSet, DeletedContactsViewSet
from .utils import create_test_individual_contact
from fecfiler.test.viewset_test import FecfilerViewSetTest

mock_results = {
    "results": [
        {"name": "LNAME, FNAME I", "candidate_id": "P60012143", "office_sought": "P"},
        {
            "name": "LNAME, FNAME",
            "candidate_id": "P60012465",
            "office_sought": "P",
        },
    ]
}


def mocked_requests_get_candidates(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    return MockResponse(mock_results, 200)


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


class ContactViewSetTest(FecfilerViewSetTest):
    fixtures = ["test_contacts", "C01234567_user_and_committee"]

    def setUp(self):
        super().setUp()

    @patch("requests.get", side_effect=mocked_requests_get_candidates)
    def test_candidate_no_candidate_id(self, mock_get):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/candidate",
            ContactViewSet,
            "candidate",
        )

        self.assertEqual(response.status_code, 400)

    @patch("requests.get", side_effect=mocked_requests_get_candidates)
    def test_candidate(self, mock_get):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/candidate?candidate_id=P60012143",
            ContactViewSet,
            "candidate",
        )
        expected_json = {
            "name": "LNAME, FNAME I",
            "candidate_id": "P60012143",
            "office_sought": "P",
        }
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding="utf8"), expected_json)

    def test_candidate_lookup_no_auth(self):
        response = self.send_viewset_get_request(
            "/api/v1/contacts/candidate_lookup?q=test",
            ContactViewSet,
            "candidate_lookup",
            authenticate=False,
        )
        self.assertEqual(response.status_code, 403)

    @patch("requests.get", side_effect=mocked_requests_get_candidates)
    def test_candidate_lookup_no_q(self, mock_get):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/candidate_lookup",
            ContactViewSet,
            "candidate_lookup",
        )
        self.assertEqual(response.status_code, 400)

    @patch("requests.get", side_effect=mocked_requests_get_candidates)
    def test_candidate_lookup_happy_path(self, mock_get):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/candidate_lookup?"
            "q=test&max_fecfile_results=5&max_fec_results=5&exclude_fec_ids=P60012143",
            ContactViewSet,
            "candidate_lookup",
        )
        expected_json = {
            "fec_api_candidates": [
                {
                    "name": "LNAME, FNAME",
                    "candidate_id": "P60012465",
                    "office_sought": "P",
                },
            ],
            "fecfile_candidates": [],
        }
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding="utf8"), expected_json)

    def test_committee_lookup_no_auth(self):
        response = self.send_viewset_get_request(
            "/api/v1/contacts/committee_lookup?q=test",
            ContactViewSet,
            "committee_lookup",
            authenticate=False,
        )
        self.assertEqual(response.status_code, 403)

    @patch("requests.get", side_effect=mocked_requests_get_committees)
    def test_committee_lookup_no_q(self, mock_get):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/committee_lookup",
            ContactViewSet,
            "committee_lookup",
        )
        self.assertEqual(response.status_code, 400)

    @patch("requests.get", side_effect=mocked_requests_get_committees)
    def test_committee_lookup_happy_path(self, mock_get):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/committee_lookup?"
            "q=test&max_fecfile_results=5&max_fec_results=5",
            ContactViewSet,
            "committee_lookup",
        )
        expected_json = {
            "fec_api_committees": [
                {"name": "BIDEN FOR PRESIDENT", "id": "C00703975", "is_active": "true"},
                {"name": "BIDEN VICTORY FUND", "id": "C00744946", "is_active": "true"},
            ],
            "fecfile_committees": [
                {
                    "deleted": None,
                    "committee_account_id": "11111111-2222-3333-4444-555555555555",
                    "id": "a03a141a-d2df-402c-93c6-e705ec6007f3",
                    "type": "COM",
                    "candidate_id": None,
                    "committee_id": "test_fec_id",
                    "name": "test name contains TestComName1",
                    "last_name": None,
                    "first_name": None,
                    "middle_name": None,
                    "prefix": None,
                    "suffix": None,
                    "street_1": "Street",
                    "street_2": None,
                    "city": "City",
                    "state": "State",
                    "zip": "12345678",
                    "employer": None,
                    "occupation": None,
                    "candidate_office": None,
                    "candidate_state": None,
                    "candidate_district": None,
                    "telephone": None,
                    "country": "Country",
                    "created": "2022-02-09T00:00:00Z",
                    "updated": "2022-02-09T00:00:00Z",
                }
            ],
        }
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding="utf8"), expected_json)

    def test_individual_lookup_no_q(self):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/individual_lookup",
            ContactViewSet,
            "individual_lookup",
        )
        self.assertEqual(response.status_code, 400)

    def xtest_individual_lookup_happy_path(self):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/individual_lookup?q=Lastname&max_fecfile_results=5",
            ContactViewSet,
            "individual_lookup",
        )
        expected_json_fragment = '"last_name": "Lastname", "first_name": "Firstname"'
        self.assertEqual(response.status_code, 200)
        self.assertIn(expected_json_fragment, str(response.content, encoding="utf8"))

    def test_organization_lookup_no_q(self):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/organization_lookup",
            ContactViewSet,
            "organization_lookup",
        )
        self.assertEqual(response.status_code, 400)

    def test_organization_lookup_happy_path(self):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/organization_lookup?q=test&max_fecfile_results=5",
            ContactViewSet,
            "organization_lookup",
        )
        expected_json_fragment = '"name": "test name contains TestOrgName1"'
        self.assertEqual(response.status_code, 200)
        self.assertIn(expected_json_fragment, str(response.content, encoding="utf8"))

    def test_get_contact_id_no_fec_id(self):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/get_contact_id/",
            ContactViewSet,
            "get_contact_id",
        )
        self.assertEqual(response.status_code, 400)

    def test_get_contact_id_finds_contact(self):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/get_contact_id/?fec_id=test_fec_id",
            ContactViewSet,
            "get_contact_id",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, uuid.UUID("a03a141a-d2df-402c-93c6-e705ec6007f3"))

    def test_get_contact_id_no_match(self):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/get_contact_id/?fec_id=id_that_doesnt_exist",
            ContactViewSet,
            "get_contact_id",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, "")

    def test_get_committee_invalid(self):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts/committee/",
            ContactViewSet,
            "committee",
        )
        self.assertEqual(response.status_code, 400)

    def test_get_committee(self):
        with patch("fecfiler.contacts.views.settings") as settings:
            settings.PRODUCTION_OPEN_FEC_API = "https://not-real.api/"
            settings.PRODUCTION_OPEN_FEC_API_KEY = "FAKE-KEY"
            expected_call = "https://not-real.api/committee/C12345678/"
            expected_params = {"api_key": "FAKE-KEY"}
            with patch("fecfiler.contacts.views.requests") as mock_requests:
                mock_requests.get = Mock()
                mock_response = Mock()
                mock_response.json = Mock()
                mock_response.json.return_value = {"results": [{"name": "TEST"}]}
                mock_requests.get.return_value = mock_response
                response = self.send_viewset_get_request_for_default(
                    "/api/v1/contacts/committee/?committee_id=C12345678",
                    ContactViewSet,
                    "committee",
                )

                self.assertEqual(response.status_code, 200)
                self.assertIn(expected_call, mock_requests.get.call_args[0])
                self.assertEqual(
                    mock_requests.get.call_args.kwargs["params"], expected_params
                )
                data = json.loads(str(response.content, encoding="utf8"))
                self.assertEqual(data["name"], "TEST")

    def test_restore_no_match(self):
        response = self.send_viewset_post_request_for_default(
            "/api/v1/contacts-deleted/restore",
            ["a5061946-0000-0000-82f6-f1782c333d70"],
            DeletedContactsViewSet,
            "restore",
        )
        self.assertEqual(response.status_code, 400)

    def test_restore(self):
        contact = Contact.objects.create(
            id="a5061946-0000-0000-82f6-f1782c333d70",
            type=Contact.ContactType.INDIVIDUAL,
            last_name="Last",
            first_name="First",
            committee_account_id="11111111-2222-3333-4444-555555555555",
        )
        contact.delete()
        deleted_contact = Contact.all_objects.get(
            id="a5061946-0000-0000-82f6-f1782c333d70"
        )
        self.assertIsNotNone(deleted_contact.deleted)
        response = self.send_viewset_post_request_for_default(
            "/api/v1/contacts-deleted/restore",
            ["a5061946-0000-0000-82f6-f1782c333d70"],
            DeletedContactsViewSet,
            "restore",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, ["a5061946-0000-0000-82f6-f1782c333d70"])

    def test_update(self):
        contact = Contact.objects.create(
            type=Contact.ContactType.INDIVIDUAL,
            last_name="Last",
            first_name="First",
            committee_account_id="11111111-2222-3333-4444-555555555555",
        )
        response = self.send_viewset_put_request_for_default(
            "/api/v1/contacts/{str(contact.id)}/",
            {
                "first_name": "Other",
                "last_name": "other",
                "street_1": "1",
                "city": "here",
                "zip": "1",
                "state": "MD",
                "country": "USA",
                "type": "IND",
            },
            ContactViewSet,
            "update",
            pk=contact.id,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["first_name"], "Other")

    def test_list_paginated(self):
        for i in range(10):
            create_test_individual_contact(
                f"last{i}", f"first{i}", "11111111-2222-3333-4444-555555555555"
            )
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts?page=1",
            ContactViewSet,
            "list",
        )
        self.assertEqual(len(response.data["results"]), 10)

    def test_list_no_pagination(self):
        response = self.send_viewset_get_request_for_default(
            "/api/v1/contacts",
            ContactViewSet,
            "list",
        )
        try:
            response.data["results"]  # A non-paginated response will throw an error here
            self.assertTrue(response is None)
        except TypeError:
            self.assertTrue(response is not None)
