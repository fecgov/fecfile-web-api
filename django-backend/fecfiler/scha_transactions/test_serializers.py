from django.test import TestCase
from .serializers import SchATransactionSerializer
from rest_framework.request import Request, HttpRequest
from fecfiler.authentication.models import Account


class SchATransactionTestCase(TestCase):
    fixtures = ["test_committee_accounts", "test_f3x_summaries"]

    def setUp(self):
        self.valid_scha_transaction = {
            "form_type": "SA11AI",
            "filer_committee_id_number": "C00123456",
            "transaction_type_identifier": "INDV_REC",
            "transaction_id": "A561234567891234",
            "entity_type": "IND",
            "contributor_organization_name": "John Smith Co",
            "contributor_first_name": "John",
            "contributor_last_name": "Smith",
            "contributor_state": "AK",
            "contributor_city": "Homer",
            "contributor_zip": "1234",
            "contributor_street_1": "1 Homer Spit Road",
            "contribution_date": "2009-01-01",
            "contribution_amount": 1234,
            "contribution_aggregate": 1234,
            "contributor_occupation": "professional",
            "contributor_employer": "boss",
            "report_id": 1,
        }

        self.invalid_scha_transaction = {
            "form_type": "invalidformtype",
            "contributor_last_name": "Validlastname",
            "transaction_type_identifier": "INDV_REC",
            "report_id": 1,
        }

        self.missing_type_transaction = {
            "form_type": "invalidformtype",
            "contributor_last_name": "Validlastname",
            "report_id": 1,
        }

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C00277616"
        self.mock_request.user = user

    def test_serializer_validate(self):
        valid_serializer = SchATransactionSerializer(
            data=self.valid_scha_transaction,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = SchATransactionSerializer(
            data=self.invalid_scha_transaction,
            context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
        self.assertIsNotNone(invalid_serializer.errors["contributor_first_name"])

    def test_no_transaction_type_identifier(self):

        missing_type_serializer = SchATransactionSerializer(
            data=self.missing_type_transaction,
            context={"request": self.mock_request},
        )
        self.assertFalse(missing_type_serializer.is_valid())
        self.assertIsNotNone(
            missing_type_serializer.errors["transaction_type_identifier"]
        )
