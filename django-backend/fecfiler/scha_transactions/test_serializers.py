from django.test import TestCase
from .serializers import SchATransactionSerializer


class SchATransactionTestCase(TestCase):
    fixtures = ["test_committee_accounts"]

    def setUp(self):
        self.valid_scha_transaction = {
            "form_type": "SA11AI",
            "filer_committee_id_number": "C00123456",
            "transaction_id": "A561234567891234",
            "entity_type": "IND",
            "contributor_organization_name": "John Smith Co",
            "contributor_first_name": "John",
            "contributor_last_name": "Smith",
        }

        self.invalid_scha_transaction = {
            "form_type": "invalidformtype",
            "contributor_last_name": "Validlastname",
        }

    def test_serializer_validate(self):
        valid_serializer = SchATransactionSerializer(
            data=self.valid_scha_transaction,
            context={"request": {"user": {"cmtee_id": "C00277616"}}},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = SchATransactionSerializer(
            data=self.invalid_scha_transaction,
            context={"request": {"user": {"cmtee_id": "C00277616"}}},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
        self.assertIsNotNone(invalid_serializer.errors["contributor_first_name"])
