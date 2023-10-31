from django.test import TestCase
from fecfiler.authentication.models import Account
from rest_framework.request import HttpRequest, Request
from fecfiler.transactions.models import Transaction

from fecfiler.transactions.schedule_c2.serializers import (
    ScheduleC2TransactionSerializer,
)
from fecfiler.transactions.schedule_c.serializers import (
    ScheduleCTransactionSerializer,
)


class ScheduleC2TransactionSerializerTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_reports",
        "test_contacts",
        "test_transaction_serializer",
        "test_memo_text",
    ]

    def setUp(self):
        self.new_contact1 = {
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
        self.new_contact2 = {
            "id": "05ab716f-c207-4dc1-8d9c-bb0fef47084a",
            "type": "IND",
            "last_name": "Smith2",
            "first_name": "John2",
            "street_1": "Street2",
            "city": "City2",
            "state": "CA",
            "zip": "12345678",
            "country": "Country",
            "created": "2022-02-09T00:00:00.000Z",
            "updated": "2022-02-09T00:00:00.000Z",
            "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
        }
        self.updated_contact = {
            "id": "00000000-6486-4062-944f-aa0c4cbe4074",
            "type": "IND",
            "last_name": "contact_1",
            "first_name": "Updated",
            "street_1": "Street",
            "city": "City",
            "state": "CA",
            "zip": "12345678",
            "country": "Country",
            "created": "2022-02-09T00:00:00.000Z",
            "updated": "2022-02-09T00:00:00.000Z",
            "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
        }

        self.valid_schedule_c_transaction = {
            "id": "a879cf45-e74a-4252-a7bf-abf379a6e88c",
            "form_type": "SC/10",
            "transaction_type_identifier": "SCHEDULE_C",
            "transaction_id": "ABCDEF0123456789",
            "entity_type": "IND",
            "lender_organization_name": "John Smith Co",
            "lender_first_name": "John",
            "lender_middle_name": "test_lmn1",
            "lender_last_name": "Smith",
            "lender_state": "AK",
            "lender_city": "Homer",
            "lender_zip": "1234",
            "lender_street_1": "1 Homer Spit Road",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "contact_1": self.new_contact1,
            "schema_name": "SchC",
        }

        self.valid_schedule_c2_transaction = {
            "form_type": "SC2/9",
            "transaction_type_identifier": "SCHEDULE_C1",
            "transaction_id": "ABCDEF0123456789",
            "back_reference_tran_id_number": "BBCDEF0123456789",
            "guarantor_last_name": "Smythe",
            "guarantor_first_name": "Fred",
            "guarantor_middle_name": "test_gmn1",
            "guarantor_state": "AK",
            "guarantor_city": "Homer",
            "guarantor_zip": "1234",
            "guarantor_street_1": "1 Homer Spit Road",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "contact_1": self.new_contact2,
            "schema_name": "SchC2",
            "loan_amount": "1000.00",
            "guaranteed_amount": "5.00",
        }

        self.updated_valid_schedule_c2_transaction = {
            "id": "249fd59f-6a97-49f8-8c7f-239279bb7bea",
            "form_type": "SC2/9",
            "transaction_type_identifier": "SCHEDULE_C1",
            "transaction_id": "ABCDEF0123456789",
            "back_reference_tran_id_number": "BBCDEF0123456789",
            "guarantor_last_name": "Smythe",
            "guarantor_first_name": "Fred",
            "guarantor_middle_name": "test_gmn1",
            "guarantor_state": "AK",
            "guarantor_city": "Homer",
            "guarantor_zip": "1234",
            "guarantor_street_1": "1 Homer Spit Road",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "contact_1": self.updated_contact,
            "schema_name": "SchC2",
            "loan_amount": "1000.00",
            "guaranteed_amount": "5.00",
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

    def test_create_and_update_with_loan_guarantor_pulled_forward(self):
        # create schedule c that gets pulled forward
        transaction = self.valid_schedule_c_transaction.copy()
        valid_serializer = ScheduleCTransactionSerializer(
            data=transaction,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        valid_serializer.create(valid_serializer.to_internal_value(transaction))
        created_instance = Transaction.objects.filter(
            schedule_c__lender_middle_name="test_lmn1"
        )
        self.assertEqual(created_instance.count(), 3)

        # test c2 create
        self.valid_schedule_c2_transaction[
            "parent_transaction_id"
        ] = created_instance[0].id
        transaction = self.valid_schedule_c2_transaction.copy()
        valid_serializer = ScheduleC2TransactionSerializer(
            data=transaction,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        valid_serializer.create(valid_serializer.to_internal_value(transaction))
        created_instance = Transaction.objects.filter(
            schedule_c2__guarantor_middle_name="test_gmn1"
        )
        self.assertEqual(created_instance.count(), 3)

        # test c2 update
        updated_transaction = self.updated_valid_schedule_c2_transaction.copy()
        updated_transaction["guaranteed_amount"] = "10.00"
        valid_serializer.update(
            created_instance[0], valid_serializer.to_internal_value(updated_transaction)
        )
        updated_instance = Transaction.objects.filter(
            schedule_c2__guaranteed_amount="10.00"
        )
        self.assertEqual(updated_instance.count(), 4)
