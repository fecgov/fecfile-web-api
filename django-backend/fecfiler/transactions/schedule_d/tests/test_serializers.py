from django.test import TestCase
from fecfiler.authentication.models import Account
from rest_framework.request import HttpRequest, Request

from fecfiler.transactions.schedule_d.serializers import ScheduleDTransactionSerializer


class ScheduleDTransactionSerializerTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_reports",
        "test_contacts",
        "test_memo_text",
    ]

    def setUp(self):
        self.new_contact = {
            "id": "9bb5c8b2-31f3-488f-84e1-a63b0133a000",
            "type": "IND",
            "last_name": "contact_1",
            "first_name": "New",
            "street_1": "Street",
            "city": "City",
            "state": "CA",
            "zip": "12345678",
            "country": "Country",
            "created": "2022-02-09T00:00:00.000Z",
            "updated": "2022-02-09T00:00:00.000Z",
            "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
        }
        self.valid_schedule_d_transaction = {
            "form_type": "SD10",
            "transaction_type_identifier": "SCHEDULE_D",
            "transaction_id": "ABCDEF0123456789",
            "entity_type": "IND",
            "creditor_organization_name": "John Smith Co",
            "creditor_first_name": "John",
            "creditor_last_name": "Smith",
            "creditor_state": "AK",
            "creditor_city": "Homer",
            "creditor_zip": "1234",
            "creditor_street_1": "1 Homer Spit Road",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "contact_1": self.new_contact,
            "schema_name": "SchD",
        }

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C00277616"
        self.mock_request.user = user

    def test_serializer_validate(self):
        valid_serializer = ScheduleDTransactionSerializer(
            data=self.valid_schedule_d_transaction,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_transaction = self.valid_schedule_d_transaction.copy()
        invalid_transaction["form_type"] = "invalidformtype"
        del invalid_transaction["creditor_first_name"]
        invalid_serializer = ScheduleDTransactionSerializer(
            data=invalid_transaction, context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
        self.assertIsNotNone(invalid_serializer.errors["creditor_first_name"])

    def test_no_creditor_first_name(self):
        missing_type = self.valid_schedule_d_transaction.copy()
        del missing_type["creditor_first_name"]
        missing_type_serializer = ScheduleDTransactionSerializer(
            data=missing_type, context={"request": self.mock_request},
        )
        self.assertFalse(missing_type_serializer.is_valid())
        self.assertIsNotNone(missing_type_serializer.errors["creditor_first_name"])
