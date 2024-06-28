from django.test import TestCase
from fecfiler.user.models import User
from rest_framework.request import HttpRequest, Request
from fecfiler.transactions.serializers import TransactionSerializer
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.views import create_committee_view


class TransactionSerializerBaseTestCase(TestCase):

    def setUp(self):
        self.missing_type_transaction = {}
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.user = User.objects.create(email="test@fec.gov", username="gov")
        create_committee_view(self.committee.id)
        self.mock_request = Request(HttpRequest())
        self.mock_request.user = self.user
        self.mock_request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }

    def test_no_transaction_type_identifier(self):
        serializer = TransactionSerializer(
            data=self.missing_type_transaction,
            context={"request": self.mock_request},
        )

        self.assertEquals(
            serializer.get_schema_name({"schema_name": "INDIVIDUAL_RECEIPT"}),
            "INDIVIDUAL_RECEIPT",
        )
