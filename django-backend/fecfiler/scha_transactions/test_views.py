import copy

from django.test import RequestFactory, TestCase
from rest_framework.test import APIClient

from ..authentication.models import Account
from .models import SchATransaction
from .views import SchATransactionViewSet


class SchATransactionsViewTest(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_contacts",
        "test_scha_transactions",
        "test_accounts",
        "test_memo_text",
    ]

    test_endpoint = "/api/v1/sch-a-transactions/"
    test_phone = "+1 1234567890"
    test_data = {
        "contact": {
            "type": "IND",
            "last_name": "test_ln1",
            "first_name": "test_ln1",
            "middle_name": "test_mn1",
            "prefix": "test_px1",
            "suffix": "test_sx1",
            "employer": "test_employer1",
            "occupation": "test_occupation1",
            "street_1": "test_streetOne1",
            "street_2": "test_streetTwo1",
            "city": "test_city1",
            "state": "AZ",
            "zip": "12345",
            "country": "USA",
            "telephone": test_phone,
        },
        "contributor_last_name": "test_ln1",
        "contributor_first_name": "test_fn1",
        "contributor_middle_name": "test_mn1",
        "contributor_prefix": "test_px1",
        "contributor_suffix": "test_sx1",
        "contributor_employer": "test_employer1",
        "contributor_occupation": "test_occupation1",
        "contributor_street_1": "test_streetOne1",
        "contributor_street_2": "test_streetTwo1",
        "contributor_city": "test_city1",
        "contributor_state": "AZ",
        "contributor_zip": "12345",
        "contribution_aggregate": "0.00",
        "contribution_amount": "12.00",
        "aggregation_group": "OTHER_RECEIPTS",
        "contribution_date": "2022-10-07",
        "entity_type": "IND",
        "filer_committee_id_number": "C00601211",
        "form_type": "SA17",
        "report": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
        "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
        "transaction_id": "C8758663365855FEAC76",
        "transaction_type_identifier": "OTHER_RECEIPT",
        "memo_text": {
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "transaction_id_number": "ABCDEF0123456789",
            "filer_committee_id_number": "C00123456",
            "rec_type":"",
            "back_reference_sched_form_name":"",
            "back_reference_sched_form_name":"",
        },
        "memo_text_id": "a12321aa-a11a-b22b-c33c-abc123321cba",
    }

    def setUp(self):
        self.f3x_id = "b6d60d2d-d926-4e89-ad4b-c47d152a66ae"
        self.f3x_2_id = "a07c8c65-1b2d-4e6e-bcaa-fa8d39e50965"
        self.f3x_transaction_count = len(
            SchATransaction.objects.filter(report_id=self.f3x_id)
        )
        self.f3x_2_transaction_count = len(
            SchATransaction.objects.filter(report_id=self.f3x_2_id)
        )

        self.memo_text = {
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "transaction_id_number": "ABCDEF0123456789",
            "filer_committee_id_number": "C00123456",
            "rec_type":"",
            "back_reference_sched_form_name":"",
            "back_reference_sched_form_name":"",
        }

        self.user = Account.objects.get(cmtee_id="C12345678")
        self.factory = RequestFactory()

    def test_view_url_exists_at_desired_location(self):
        request = self.factory.get(
            f"/api/v1/sch-a-transactions/?report_id={self.f3x_id}"
        )
        request.user = self.user
        response = SchATransactionViewSet.as_view({"get": "list"})(request)
        self.assertEqual(response.status_code, 200)

    def test_is_paginated(self):
        request = self.factory.get(
            f"/api/v1/sch-a-transactions/?report_id={self.f3x_id}"
        )
        request.user = self.user
        response = SchATransactionViewSet.as_view({"get": "list"})(request)

        response.render()
        parsed_response = response.data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(parsed_response["count"], self.f3x_transaction_count)
        self.assertEqual(len(parsed_response["results"]), 10)

    def test_only_from_one_report(self):
        responses = []
        for url in [
            f"/api/v1/sch-a-transactions/?report_id={self.f3x_id}",
            f"/api/v1/sch-a-transactions/?report_id={self.f3x_2_id}",
        ]:
            request = self.factory.get(url)
            request.user = self.user
            response = SchATransactionViewSet.as_view({"get": "list"})(request)

            response.render()
            responses.append(response.data)

        self.assertNotEqual(responses[0]["count"], responses[1]["count"])

    def test_create_new_scha_transaction_create_ind_contact_no_transaction(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        data = {
            "contact": {
                "type": "IND",
                "last_name": "test_ln1",
                "first_name": "test_ln1",
                "middle_name": "test_mn1",
                "prefix": "test_px1",
                "suffix": "test_sx1",
                "employer": "test_employer1",
                "occupation": "test_occupation1",
                "street_1": "test_streetOne1",
                "street_2": "test_streetTwo1",
                "city": "test_city1",
                "state": "AZ",
                "zip": "12345",
                "country": "USA",
                "telephone": self.test_phone,
            }
        }
        response = client.post(self.test_endpoint, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_create_new_scha_transaction_create_ind_contact_no_contact_id(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        data = {
            "contributor_last_name": "test_ln1",
            "contributor_first_name": "test_fn1",
            "contributor_middle_name": "test_mn1",
            "contributor_prefix": "test_px1",
            "contributor_suffix": "test_sx1",
            "contributor_employer": "test_employer1",
            "contributor_occupation": "test_occupation1",
            "contributor_street_1": "test_streetOne1",
            "contributor_street_2": "test_streetTwo1",
            "contributor_city": "test_city1",
            "contributor_state": "AZ",
            "contributor_zip": "12345",
            "contribution_aggregate": "0.00",
            "contribution_amount": "12.00",
            "contribution_date": "2022-10-07",
            "entity_type": "IND",
            "filer_committee_id_number": "C00601211",
            "form_type": "SA17",
            "report": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "transaction_id": "C8758663365855FEAC76",
            "transaction_type_identifier": "OTHER_RECEIPT",
        }
        response = client.post(self.test_endpoint, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_create_new_scha_transaction_create_ind_contact_invalid_contact(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        data = copy.deepcopy(self.test_data)
        del data["contact"]["last_name"]
        response = client.post(self.test_endpoint, data, format="json")
        self.assertEqual(response.status_code, 400)

    def test_create_new_scha_transaction_create_ind_contact(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        data = copy.deepcopy(self.test_data)
        response = client.post(self.test_endpoint, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_create_new_scha_transaction_update_ind_contact(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        data = copy.deepcopy(self.test_data)
        data["contact_id"] = "a5061946-93ef-47f4-82f6-f1782c333d70"
        response = client.post(self.test_endpoint, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_create_new_scha_transaction_create_cmtee_contact(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        data = {
            "contact": {
                "type": "COM",
                "name": "test_orgname1",
                "committee_id": "C12345678",
                "street_1": "test_streetOne1",
                "street_2": "test_streetTwo1",
                "city": "test_city1",
                "state": "AZ",
                "zip": "12345",
                "country": "USA",
                "telephone": self.test_phone,
            },
            "donor_committee_fec_id": "C12345678",
            "contributor_organization_name": "test_orgname1",
            "contributor_street_1": "test_streetOne1",
            "contributor_street_2": "test_streetTwo1",
            "contributor_city": "test_city1",
            "contributor_state": "AZ",
            "contributor_zip": "test_zip1",
            "contribution_aggregate": "0.00",
            "aggregation_group": "OTHER_RECEIPTS",
            "contribution_amount": "12.00",
            "contribution_date": "2022-10-07",
            "entity_type": "COM",
            "filer_committee_id_number": "C00601211",
            "form_type": "SA17",
            "report": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "transaction_id": "C8758663365855FEAC76",
            "transaction_type_identifier": "OTHER_RECEIPT",
            "contact_id": "a03a141a-d2df-402c-93c6-e705ec6007f3",
            "memo_text": self.memo_text,
            "memo_text_id": "a12321aa-a11a-b22b-c33c-abc123321cba",
        }
        response = client.post(self.test_endpoint, data, format="json")
        self.assertEqual(response.status_code, 201)

    def test_create_new_scha_transaction_create_org_contact(self):
        client = APIClient()
        client.force_authenticate(user=self.user)
        data = {
            "contact": {
                "type": "ORG",
                "name": "test_orgname1",
                "street_1": "test_streetOne1",
                "street_2": "test_streetTwo1",
                "city": "test_city1",
                "state": "AZ",
                "zip": "12345",
                "country": "USA",
                "telephone": self.test_phone,
            },
            "contributor_organization_name": "test_orgname1",
            "contributor_street_1": "test_streetOne1",
            "contributor_street_2": "test_streetTwo1",
            "contributor_city": "test_city1",
            "contributor_state": "AZ",
            "contributor_zip": "test_zip1",
            "contribution_aggregate": "0.00",
            "aggregation_group": "OTHER_RECEIPTS",
            "contribution_amount": "12.00",
            "contribution_date": "2022-10-07",
            "entity_type": "ORG",
            "filer_committee_id_number": "C00601211",
            "form_type": "SA17",
            "report": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "transaction_id": "C8758663365855FEAC76",
            "transaction_type_identifier": "OTHER_RECEIPT",
            "contact_id": "5720a518-6486-4062-944f-aa0c4cbe4073",
            "memo_text": self.memo_text,
            "memo_text_id": "a12321aa-a11a-b22b-c33c-abc123321cba",
        }
        response = client.post(self.test_endpoint, data, format="json")
        self.assertEqual(response.status_code, 201)
