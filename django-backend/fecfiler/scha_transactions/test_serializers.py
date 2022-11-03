from django.test import TestCase
from fecfiler.authentication.models import Account
from rest_framework.request import HttpRequest, Request

from .models import SchATransaction
from .serializers import (SchATransactionParentSerializer,
                          SchATransactionSerializer)


class SchATransactionTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_contacts",
        "test_memo_text"
    ]

    def setUp(self):
        self.test_contact = {
            "id": "a5061946-93ef-47f4-82f6-f1782c333d70",
            "type": "IND",
            "last_name": "Lastname",
            "first_name": "Firstname",
            "street_1": "Street",
            "city": "City",
            "state": "CA",
            "zip": "12345678",
            "country": "Country",
            "created": "2022-02-09T00:00:00.000Z",
            "updated": "2022-02-09T00:00:00.000Z",
            "committee_account_id": "735db943-9446-462a-9be0-c820baadb622"
        }

        self.memo_text = {
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "transaction_id_number": "ABCDEF0123456789",
            "filer_committee_id_number": "C00123456",
            "rec_type": "",
            "back_reference_sched_form_name": "",
        }

        self.valid_scha_transaction = {
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
            "contact_id": "a5061946-93ef-47f4-82f6-f1782c333d70",
            "memo_text": self.memo_text,
            "memo_text_id": "a12321aa-a11a-b22b-c33c-abc123321cba",
            "contact": self.test_contact.copy(),
        }

        self.invalid_scha_transaction = {
            "form_type": "invalidformtype",
            "contributor_last_name": "Validlastname",
            "transaction_id": "ABCDEF0123456789",
            "transaction_type_identifier": "INDIVIDUAL_RECEIPT",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "contact_id": "a5061946-93ef-47f4-82f6-f1782c333d70",
            "contact": self.test_contact.copy(),
            "memo_text": self.memo_text,
            "memo_text_id": "a12321aa-a11a-b22b-c33c-abc123321cba",
        }

        self.missing_type_transaction = {
            "form_type": "invalidformtype",
            "transaction_id": "ABCDEF0123456789",
            "contributor_last_name": "Validlastname",
            "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
            "contact_id": "a5061946-93ef-47f4-82f6-f1782c333d70",
            "contact": self.test_contact.copy(),
            "memo_text": self.memo_text,
            "memo_text_id": "a12321aa-a11a-b22b-c33c-abc123321cba",
        }

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C00277616"
        self.mock_request.user = user

    def test_serializer_validate(self):
        valid_serializer = SchATransactionSerializer(
            data=self.valid_scha_transaction, context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = SchATransactionSerializer(
            data=self.invalid_scha_transaction, context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
        self.assertIsNotNone(invalid_serializer.errors["contributor_first_name"])

    def test_no_transaction_type_identifier(self):

        missing_type_serializer = SchATransactionSerializer(
            data=self.missing_type_transaction, context={"request": self.mock_request},
        )
        self.assertFalse(missing_type_serializer.is_valid())
        self.assertIsNotNone(
            missing_type_serializer.errors["transaction_type_identifier"]
        )

    def test_parent(self):
        parent = self.valid_scha_transaction.copy()
        parent["transaction_type_identifier"] = "EARMARK_RECEIPT"
        parent["contribution_purpose_descrip"] = "test"
        child = self.valid_scha_transaction.copy()
        child["transaction_type_identifier"] = "EARMARK_MEMO"
        child["contribution_purpose_descrip"] = "test"
        child["back_reference_sched_name"] = "test"
        child["back_reference_tran_id_number"] = "test"
        child["memo_code"] = True
        parent["children"] = [child]
        serializer = SchATransactionParentSerializer(
            data=parent, context={"request": self.mock_request},
        )
        self.assertTrue(serializer.is_valid(raise_exception=True))
        serializer.create(serializer.to_internal_value(parent))
        parent_instance = SchATransaction.objects.filter(
            transaction_type_identifier="EARMARK_RECEIPT"
        )[0]
        children = SchATransaction.objects.filter(parent_transaction=parent_instance)
        self.assertNotEqual(children.count(), 0)

        parent = parent_instance.__dict__.copy()
        child = children[0].__dict__.copy()
        parent["contribution_purpose_descrip"] = "updated parent"
        parent["memo_text"] = self.memo_text
        child["contribution_purpose_descrip"] = "updated child"
        child["memo_text"] = self.memo_text
        parent["children"] = [child]
        parent["contact"] = self.test_contact.copy()
        child["contact"] = self.test_contact.copy()
        parent_instance = serializer.update(
            parent_instance, serializer.to_internal_value(parent)
        )
        self.assertEqual(parent_instance.contribution_purpose_descrip, "updated parent")

        children = SchATransaction.objects.filter(parent_transaction_id=parent_instance)
        self.assertEqual(children[0].contribution_purpose_descrip, "updated child")

        old_child_id = children[0].id
        child["id"] = None
        child["contribution_purpose_descrip"] = "very new child"
        parent["children"] = [child]
        parent_instance = serializer.update(
            parent_instance, serializer.to_internal_value(parent)
        )
        children = SchATransaction.objects.filter(parent_transaction_id=parent_instance)
        self.assertEqual(children[0].contribution_purpose_descrip, "very new child")
        with self.assertRaises(SchATransaction.DoesNotExist):
            SchATransaction.objects.get(id=old_child_id)
