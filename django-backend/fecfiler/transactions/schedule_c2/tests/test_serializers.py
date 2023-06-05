from django.test import TestCase
from fecfiler.authentication.models import Account
from rest_framework.request import HttpRequest, Request

from fecfiler.transactions.schedule_c2.serializers import (
    ScheduleC2TransactionSerializer,
)


class ScheduleC2TransactionSerializerTestCase(TestCase):
    def setUp(self):
        self.new_contact = {
            "id": "9bb5c8b2-31f3-488f-84e1-a63b0133a000",
            "type": "IND",
            "last_name": "Smith",
            "first_name": "John",
            "street_1": "Street",
            "city": "City",
            "state": "CA",
            "zip": "12345678",
            "country": "Country",
            "created": "2022-02-09T00:00:00.000Z",
            "updated": "2022-02-09T00:00:00.000Z",
            "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
        }
        self.valid_schedule_c2_transaction = {
            "form_type": "SC2/9",
            "transaction_type_identifier": "SCHEDULE_C1",
            "transaction_id": "ABCDEF0123456789",
            "back_reference_tran_id_number": "BBCDEF0123456789",
            "guarantor_last_name": "Smythe",
            "guarantor_first_name": "Fred",
            "guarantor_state": "AK",
            "guarantor_city": "Homer",
            "guarantor_zip": "1234",
            "guarantor_street_1": "1 Homer Spit Road",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "contact": self.new_contact,
            "schema_name": "SchC2",
            "loan_amount": "1000.00",
        }

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C00277616"
        self.mock_request.user = user

    def test_serializer_validate(self):
        valid_serializer = ScheduleC2TransactionSerializer(
            data=self.valid_schedule_c2_transaction,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_transaction = self.valid_schedule_c2_transaction.copy()
        invalid_transaction["form_type"] = "invalidformtype"
        del invalid_transaction["guarantor_last_name"]
        invalid_serializer = ScheduleC2TransactionSerializer(
            data=invalid_transaction, context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
        self.assertIsNotNone(invalid_serializer.errors["guarantor_last_name"])

    def test_no_guarantor_last_name(self):
        missing_type = self.valid_schedule_c2_transaction.copy()
        del missing_type["guarantor_last_name"]
        missing_type_serializer = ScheduleC2TransactionSerializer(
            data=missing_type, context={"request": self.mock_request},
        )
        self.assertFalse(missing_type_serializer.is_valid())
        self.assertIsNotNone(missing_type_serializer.errors["guarantor_last_name"])
