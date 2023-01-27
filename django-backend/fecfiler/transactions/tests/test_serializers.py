from django.test import TestCase
from fecfiler.authentication.models import Account
from rest_framework.request import HttpRequest, Request
from rest_framework.exceptions import ValidationError

from fecfiler.transactions.serializers import TransactionBaseSerializer


class TransactionSerializerBaseTestCase(TestCase):
    def setUp(self):
        self.missing_type_transaction = {}

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C00277616"
        self.mock_request.user = user

    def test_no_transaction_type_identifier(self):

        serializer = TransactionBaseSerializer(
            data=self.missing_type_transaction,
            context={"request": self.mock_request},
        )
        with self.assertRaises(ValidationError):
            serializer.get_schema_name({}),

        self.assertEquals(
            serializer.get_schema_name(
                {"schema_name": "INDIVIDUAL_RECEIPT"}
            ),
            "INDIVIDUAL_RECEIPT",
        )
