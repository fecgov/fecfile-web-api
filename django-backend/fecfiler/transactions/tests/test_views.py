from django.test import TestCase
from django.test.client import RequestFactory
from fecfiler.authentication.models import Account
import json

from fecfiler.transactions.views import save_transaction


class TransactionViewsTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_reports",
    ]

    def setUp(self):
        self.factory = RequestFactory()
        self.user = Account()
        self.user.cmtee_id = "C00601211"

    def test_save_new_transaction_pair(self):
        payload = json.load(
            open("fecfiler/transactions/fixtures/payload_transaction_pair.json")
        )
        request = self.factory.post(
            "/api/v1/transactions/save",
            json.dumps(payload),
            content_type="application/json",
        )
        request.user = self.user
        request.data = payload
        request.query_params = {}
        response = save_transaction(request)
        self.assertEqual("John", response.data["contributor_first_name"])
        self.assertEqual("Smith", response.data["contributor_last_name"])
