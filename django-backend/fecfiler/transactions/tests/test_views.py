from django.test import TestCase
from django.test.client import RequestFactory
from fecfiler.user.models import User
import json
from copy import deepcopy
from fecfiler.transactions.views import TransactionViewSet
from fecfiler.transactions.models import Transaction
from fecfiler.committee_accounts.views import create_committee_view


class TransactionViewsTestCase(TestCase):
    fixtures = [
        "C01234567_user_and_committee",
        "test_f3x_reports",
        "test_transaction_views_transactions",
        "test_election_aggregation_data",
    ]

    json_content_type = "application/json"

    @classmethod
    def setUpClass(cls):
        return super().setUpClass()

    def setUp(self):
        print("SETUP TEST_VEW")
        create_committee_view("11111111-2222-3333-4444-555555555555")
        self.factory = RequestFactory()
        self.user = User.objects.get(id="12345678-aaaa-bbbb-cccc-111122223333")
        self.payloads = json.load(
            open("fecfiler/transactions/fixtures/view_payloads.json")
        )

    def request(self, payload, params={}):
        request = self.factory.post(
            "/api/v1/transactions",
            json.dumps(payload),
            content_type=self.json_content_type,
        )
        request.user = self.user
        request.data = deepcopy(payload)
        request.query_params = params
        request.session = {
            "committee_uuid": "11111111-2222-3333-4444-555555555555",
            "committee_id": "C01234567",
        }
        return request

    def test_save_transaction_pair(self):
        request = self.request(self.payloads["IN_KIND"])
        transaction = TransactionViewSet().save_transaction(request.data, request)
        self.assertEqual("John", transaction.contact_1.first_name)
        self.assertEqual("Smith", transaction.contact_1.last_name)

    def test_update(self):
        request = self.request(self.payloads["IN_KIND"])
        transaction = TransactionViewSet().save_transaction(request.data, request)
        updated_payload = deepcopy(self.payloads["IN_KIND"])
        updated_payload["id"] = str(transaction.id)
        updated_payload["contribution_amount"] = 999
        updated_payload["children"][0]["id"] = str(transaction.children[0].id)
        updated_payload["children"][0]["expenditure_amount"] = 999
        request = self.request(updated_payload)
        transaction = TransactionViewSet().save_transaction(request.data, request)
        updated_transaction = Transaction.objects.get(id=transaction.id)
        self.assertEqual(updated_transaction.schedule_a.contribution_amount, 999)
        self.assertEqual(
            updated_transaction.children[0].schedule_b.expenditure_amount, 999
        )

    def test_get_queryset(self):
        view_set = TransactionViewSet()
        view_set.request = self.request({}, {"schedules": "A,B,C,C2,D,E"})
        self.assertEqual(view_set.get_queryset().count(), 12)
        view_set.request = self.request({}, {"schedules": "A,B,D,E"})
        self.assertEqual(view_set.get_queryset().count(), 10)
        view_set.request = self.request({}, {"schedules": ""})
        self.assertEqual(view_set.get_queryset().count(), 0)

    def test_get_previous_entity(self):
        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        view_set.request = self.request(
            {}, {"contact_1_id": "00000000-6486-4062-944f-aa0c4cbe4073"}
        )
        # leave out required params
        response = view_set.previous_transaction_by_entity(view_set.request)
        self.assertEqual(response.status_code, 400)

        response = view_set.previous_transaction_by_entity(
            self.request(
                {},
                {
                    "contact_1_id": "00000000-6486-4062-944f-aa0c4cbe4073",
                    "date": "2023-09-20",
                    "aggregation_group": "GENERAL_DISBURSEMENT",
                },
            )
        )
        self.assertEqual(response.data["date"], "2023-09-02")

        response = view_set.previous_transaction_by_entity(
            self.request(
                {},
                {
                    "contact_1_id": "00000000-6486-4062-944f-aa0c4cbe4073",
                    "date": "2024-09-20",
                    "aggregation_group": "GENERAL_DISBURSEMENT",
                },
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_get_previous_election(self):
        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        view_set.request = self.request(
            {},
            {
                "date": "2023-09-20",
                "aggregation_group": "INDEPENDENT_EXPENDITURE",
                "election_code": "C2012",
                "candidate_office": "S",
            },
        )
        # leave out required params
        response = view_set.previous_transaction_by_election(view_set.request)
        self.assertEqual(response.status_code, 400)
        view_set.request = self.request(
            {},
            {
                "date": "2023-09-20",
                "aggregation_group": "INDEPENDENT_EXPENDITURE",
                "election_code": "C2012",
                "candidate_office": "H",
                "candidate_state": "AK",
            },
        )
        # leave out required params
        response = view_set.previous_transaction_by_election(view_set.request)
        self.assertEqual(response.status_code, 400)

        view_set.request = self.request(
            {},
            {
                "date": "2023-10-31",
                "aggregation_group": "INDEPENDENT_EXPENDITURE",
                "election_code": "C2012",
                "candidate_office": "S",
                "candidate_state": "AK",
            },
        )
        response = view_set.previous_transaction_by_election(view_set.request)
        self.assertEqual(response.data["date"], "2023-10-31")

    def test_inherited_election_aggregate(self):
        request = self.factory.get(
            "/api/v1/transactions/aaaaaaaa-607f-4f5d-bfb4-0fa1776d4e35/"
        )
        request.user = self.user
        request.query_params = {}
        request.data = {}
        request.session = {
            "committee_uuid": "11111111-2222-3333-4444-555555555555",
            "committee_id": "C01234567",
        }

        view = TransactionViewSet
        view.request = request
        response = view.as_view({"get": "retrieve"})(
            request, pk="aaaaaaaa-607f-4f5d-bfb4-0fa1776d4e35"
        )
        transaction = response.data
        self.assertEqual(transaction.get("calendar_ytd_per_election_office"), "58.00")

    def test_multisave_transactions(self):
        txn1 = deepcopy(self.payloads["IN_KIND"])
        txn1["contributor_last_name"] = "one"
        txn2 = deepcopy(self.payloads["IN_KIND"])
        txn2["contributor_last_name"] = "two"
        txn3 = deepcopy(self.payloads["IN_KIND"])
        txn3["contributor_last_name"] = "three"

        payload = [txn1, txn2, txn3]

        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        request = self.factory.put(
            "/api/v1/transactions/multisave/",
            json.dumps(payload),
            content_type=self.json_content_type,
        )
        request.user = self.user
        request.data = deepcopy(payload)
        view_set.request = request

        view_set = TransactionViewSet()
        response = view_set.save_transactions(self.request(payload))
        transactions = response.data
        self.assertEqual(len(transactions), 3)
        # self.assertEqual("one", transactions[0]["contributor_last_name"])

    def test_reatt_redes_multisave_transactions(self):
        txn1 = deepcopy(self.payloads["IN_KIND"])
        txn1["contributor_last_name"] = "one"
        txn2 = deepcopy(self.payloads["IN_KIND"])
        txn2["contributor_last_name"] = "two"
        txn3 = deepcopy(self.payloads["IN_KIND"])
        txn3["contributor_last_name"] = "three"
        txn2["children"] = [txn3]
        payload = [txn1, txn2]

        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        request = self.factory.put(
            "/api/v1/transactions/multisave/",
            json.dumps(payload),
            content_type=self.json_content_type,
        )
        request.user = self.user
        request.data = deepcopy(payload)
        view_set.request = request

        view_set = TransactionViewSet()
        response = view_set.save_reatt_redes_transactions(self.request(payload))
        transactions = response.data
        self.assertEqual(len(transactions), 2)
