from unittest.mock import patch

from django.test import TestCase, override_settings
from fecfiler.authentication.models import Account
from fecfiler.transactions.schedule_a.serializers import (
    ScheduleATransactionSerializer)
from rest_framework.request import HttpRequest, Request


class ScheduleATransactionSerializerBaseTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_contacts",
        "test_memo_text",
        "test_transaction_manager_transactions",
    ]

    def setUp(self):
        self.new_contact = {
            "id": "9bb5c8b2-31f3-488f-84e1-a63b0133a000",
            "type": "IND",
            "last_name": "Contact",
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

        self.updated_contact = {
            "id": "1578e90c-5348-4afa-9db8-cbeddf9aa701",
            "type": "IND",
            "last_name": "Contact",
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

        self.new_memo_text = {
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "transaction_id_number": "ABCDEF0123456789",
            "filer_committee_id_number": "C00123456",
            "rec_type": "",
            "memo4000": "new memo text",
            "back_reference_sched_form_name": "",
        }
        self.valid_schedule_a_transaction = {
            "form_type": "SA",
            "filer_committee_id_number": "C00123456",
            "transaction_type_identifier": "SchA",
            "transaction_id": "ABCDEF0123456789",
            "entity_type": "IND",
            "contributor_organization_name": "John Smith Co",
            "contributor_last_name": "John",
            "contributor_first_name": "Smith",
            "contributor_state": "AK",
            "contributor_city": "Homer",
            "contributor_zip": "1234",
            "contributor_street_1": "1 Homer Spit Road",
            "contribution_date": "2009-01-01",
            "contribution_amount": 1234,
            "aggregation_group": "GENERAL",
            "contributor_occupation": "professional",
            "contributor_employer": "boss",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "contact": self.new_contact,
            "schema_name": "SchA",
        }
        self.new_schedule_a_transaction_updated_contact = {
            "form_type": "SA",
            "filer_committee_id_number": "C00123456",
            "transaction_type_identifier": "SchA",
            "transaction_id": "ABCDEF0123456789",
            "entity_type": "IND",
            "contributor_organization_name": "John Smith Co",
            "contributor_last_name": "John",
            "contributor_first_name": "Smith",
            "contributor_state": "AK",
            "contributor_city": "Homer",
            "contributor_zip": "1234",
            "contributor_street_1": "1 Homer Spit Road",
            "contribution_date": "2009-01-01",
            "contribution_amount": 1234,
            "aggregation_group": "GENERAL",
            "contributor_occupation": "professional",
            "contributor_employer": "boss",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "contact": self.updated_contact,
            "contact_id": "1578e90c-5348-4afa-9db8-cbeddf9aa701",
            "schema_name": "SchA",
        }

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C12345678"
        self.mock_request.user = user

    def test_serializer_validate(self):
        valid_serializer = ScheduleATransactionSerializer(
            data=self.valid_schedule_a_transaction,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_transaction = self.valid_schedule_a_transaction.copy()
        invalid_transaction["form_type"] = "invalidformtype"
        del invalid_transaction["contributor_first_name"]
        invalid_serializer = ScheduleATransactionSerializer(
            data=invalid_transaction,
            context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
        self.assertIsNotNone(invalid_serializer.errors["contributor_first_name"])

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('fecfiler.transactions.schedule_a.tasks.update_future_transaction_contacts')
    def test_serializer_create_with_updated_contact(self, task):
        test_serializer = ScheduleATransactionSerializer(
            data=self.new_schedule_a_transaction_updated_contact,
            context={"request": self.mock_request},
        )
        retval = test_serializer.create(
            self.new_schedule_a_transaction_updated_contact
        )
        self.assertTrue(retval)

    def test_serializer_update(self):
        test_serializer = ScheduleATransactionSerializer(
            data=self.new_schedule_a_transaction_updated_contact,
            context={"request": self.mock_request},
        )
        self.assertTrue(test_serializer.is_valid(raise_exception=True))
