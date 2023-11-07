from django.test import TestCase
from fecfiler.authentication.models import Account
from rest_framework.request import HttpRequest, Request
from fecfiler.transactions.serializers import TransactionSerializer


class TransactionSerializerBaseTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_reports",
        "test_transaction_serializer",
    ]

    def setUp(self):
        self.missing_type_transaction = {}

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C00277616"
        self.mock_request.user = user

    def test_no_transaction_type_identifier(self):
        serializer = TransactionSerializer(
            data=self.missing_type_transaction,
            context={"request": self.mock_request},
        )

        self.assertEquals(
            serializer.get_schema_name({"schema_name": "INDIVIDUAL_RECEIPT"}),
            "INDIVIDUAL_RECEIPT",
        )
