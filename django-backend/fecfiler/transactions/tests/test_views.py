from django.test import TestCase
from django.test.client import RequestFactory
from fecfiler.authentication.models import Account
import json

from fecfiler.transactions.views import save_transaction_pair


class TransactionViewsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = Account.objects.get(email="test1@test.com")

    def test_save_new_transaction_pair(self):
        # payload = json.load(
        #     open("fecfiler/transactions/fixtures/test_transaction_pair_payload.json")
        # )
        payload = json.load(
            open("fecfiler/transactions/fixtures/test_transaction_pair_payload.json")
        )
        request = self.factory.post(
            "/api/v1/transactions/save-pair",
            json.dumps(payload),
            content_type="application/json",
        )
        request.user = self.user
        request.data = payload
        request.query_params = {}
        response = save_transaction_pair(request)
        self.assertEqual("foo", response.data["contributor_first_name"])

