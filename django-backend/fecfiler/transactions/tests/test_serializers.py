from django.test import TestCase
from fecfiler.user.models import User
from rest_framework.request import HttpRequest, Request
from fecfiler.transactions.serializers import TransactionSerializer


class TransactionSerializerBaseTestCase(TestCase):
    fixtures = [
        "C01234567_user_and_committee",
        "test_f3x_reports",
        "test_transaction_serializer",
    ]

    def setUp(self):
        self.missing_type_transaction = {}

        self.mock_request = Request(HttpRequest())
        self.mock_request.user = User.objects.get(
            id="12345678-aaaa-bbbb-cccc-111122223333"
        )

    def test_no_transaction_type_identifier(self):
        serializer = TransactionSerializer(
            data=self.missing_type_transaction,
            context={"request": self.mock_request},
        )

        self.assertEquals(
            serializer.get_schema_name({"schema_name": "INDIVIDUAL_RECEIPT"}),
            "INDIVIDUAL_RECEIPT",
        )
