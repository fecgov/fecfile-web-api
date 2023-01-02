from django.test import TestCase
from fecfiler.authentication.models import Account
from rest_framework.request import HttpRequest, Request

from fecfiler.transactions.schedule_a.models import ScheduleATransaction
from fecfiler.transactions.schedule_a.serializers import (
    ScheduleATransactionSerializerBase,
    ScheduleATransactionSerializer,
)


class ScheduleATransactionSerializerBaseTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_contacts",
        "test_memo_text",
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

        self.new_memo_text = {
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "transaction_id_number": "ABCDEF0123456789",
            "filer_committee_id_number": "C00123456",
            "rec_type": "",
            "memo4000": "new memo text",
            "back_reference_sched_form_name": "",
        }
        self.valid_schedule_a_transaction = {
            "form_type": "SA11AI",
            "filer_committee_id_number": "C00123456",
            "transaction_type_identifier": "INDIVIDUAL_RECEIPT",
            "transaction_id": "ABCDEF0123456789",
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
            "aggregation_group": "GENERAL",
            "contributor_occupation": "professional",
            "contributor_employer": "boss",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "contact": self.new_contact,
        }

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C00277616"
        self.mock_request.user = user

    def test_serializer_validate(self):
        valid_serializer = ScheduleATransactionSerializerBase(
            data=self.valid_schedule_a_transaction,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_transaction = self.valid_schedule_a_transaction.copy()
        invalid_transaction["form_type"] = "invalidformtype"
        del invalid_transaction["contributor_first_name"]
        invalid_serializer = ScheduleATransactionSerializerBase(
            data=invalid_transaction,
            context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
        self.assertIsNotNone(invalid_serializer.errors["contributor_first_name"])

    def test_no_transaction_type_identifier(self):
        missing_type = self.valid_schedule_a_transaction.copy()
        del missing_type["transaction_type_identifier"]
        missing_type_serializer = ScheduleATransactionSerializerBase(
            data=missing_type,
            context={"request": self.mock_request},
        )
        self.assertFalse(missing_type_serializer.is_valid())
        self.assertIsNotNone(
            missing_type_serializer.errors["transaction_type_identifier"]
        )

    def test_parent(self):
        parent = self.valid_schedule_a_transaction.copy()
        parent["transaction_type_identifier"] = "EARMARK_RECEIPT"
        parent["contribution_purpose_descrip"] = "test"
        child = self.valid_schedule_a_transaction.copy()
        child["transaction_type_identifier"] = "EARMARK_MEMO"
        child["contribution_purpose_descrip"] = "test"
        child["back_reference_sched_name"] = "test"
        child["back_reference_tran_id_number"] = "test"
        child["memo_code"] = True
        parent["children"] = [child]
        serializer = ScheduleATransactionSerializer(
            data=parent,
            context={"request": self.mock_request},
        )
        self.assertTrue(serializer.is_valid(raise_exception=True))
        serializer.create(serializer.to_internal_value(parent))
        parent_instance = ScheduleATransaction.objects.filter(
            transaction_type_identifier="EARMARK_RECEIPT"
        )[0]
        children = ScheduleATransaction.objects.filter(
            parent_transaction=parent_instance
        )
        self.assertNotEqual(children.count(), 0)

        parent = parent_instance.__dict__.copy()
        child = children[0].__dict__.copy()
        parent["contribution_purpose_descrip"] = "updated parent"
        child["contribution_purpose_descrip"] = "updated child"
        parent["children"] = [child]
        parent_instance = serializer.update(
            parent_instance, serializer.to_internal_value(parent)
        )
        self.assertEqual(parent_instance.contribution_purpose_descrip, "updated parent")

        children = ScheduleATransaction.objects.filter(
            parent_transaction_id=parent_instance
        )
        self.assertEqual(children[0].contribution_purpose_descrip, "updated child")

        child["id"] = None
        child["contribution_purpose_descrip"] = "very new child"
        parent["children"] = [child]
        parent_instance = serializer.update(
            parent_instance, serializer.to_internal_value(parent)
        )
        children = ScheduleATransaction.objects.filter(
            parent_transaction_id=parent_instance
        )
        self.assertEqual(children[0].contribution_purpose_descrip, "very new child")
        self.assertEqual(children[1].contribution_purpose_descrip, "updated child")
