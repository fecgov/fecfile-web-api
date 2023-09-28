from django.test import TestCase
from fecfiler.authentication.models import Account
from rest_framework.request import HttpRequest, Request
from rest_framework.exceptions import ValidationError

from fecfiler.transactions.models import Transaction
from fecfiler.transactions.serializers import TransactionSerializerBase
from fecfiler.transactions.schedule_a.serializers import ScheduleATransactionSerializer


class TransactionSerializerBaseTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_transaction_serializer",
    ]

    def setUp(self):
        self.missing_type_transaction = {}

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C00277616"
        self.mock_request.user = user

    def test_no_transaction_type_identifier(self):
        serializer = TransactionSerializerBase(
            data=self.missing_type_transaction, context={"request": self.mock_request},
        )
        with self.assertRaises(ValidationError):
            serializer.get_schema_name({}),

        self.assertEquals(
            serializer.get_schema_name({"schema_name": "INDIVIDUAL_RECEIPT"}),
            "INDIVIDUAL_RECEIPT",
        )

    def test_propagation_existing_transaction(self):
        valid_serializer = ScheduleATransactionSerializer(
            Transaction.objects.get(id="12345678-0000-0000-0000-9509df48e1aa"),
            data={
                "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
                "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
                "contact_1_id": "00000000-6486-4062-944f-aa0c4cbe4073",
                "contact_1": {
                    "id": "00000000-6486-4062-944f-aa0c4cbe4073",
                    "type": "ORG",
                    "name": "new name",
                    "street_1": "original st",
                    "city": "original city",
                    "state": "MD",
                    "zip": "123",
                    "country": "original country",
                    "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
                },
                "form_type": "SA15",
                "id": "12345678-0000-0000-0000-9509df48e1aa",
                "transaction_type_identifier": "OFFSET_TO_OPERATING_EXPENDITURES",
                "schema_name": "OFFSET_TO_OPERATING_EXPENDITURES",
                "fields_to_validate": ["contribution_amount"],
                "contribution_amount": 1,
                "contribution_date": "2022-01-01",
                "contributor_street_1": "original st",
                "contributor_city": "original city",
                "contributor_state": "original state",
                "contributor_zip": "original zip",
                "contributor_organization_name": "new name",
            },
            context={"request": self.mock_request},
        )
        valid_serializer.is_valid()
        valid_serializer.save()
        second_transaction = Transaction.objects.get(
            id="87654321-0000-0000-0000-9509df48e1aa"
        )
        self.assertEqual(
            "new name", second_transaction.schedule_b.payee_organization_name
        )
        third_transaction = Transaction.objects.get(
            id="33333333-0000-0000-0000-9509df48e1aa"
        )
        self.assertEqual(
            "new name", third_transaction.schedule_a.contributor_organization_name
        )

    def test_propagation_new_transaction(self):
        valid_serializer = ScheduleATransactionSerializer(
            data={
                "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
                "report_id": "b6d60d2d-d926-4e89-ad4b-c47d152a66ae",
                "contact_1_id": "00000000-6486-4062-944f-aa0c4cbe4073",
                "contact_1": {
                    "id": "00000000-6486-4062-944f-aa0c4cbe4073",
                    "type": "ORG",
                    "name": "orignial name",
                    "street_1": "original st",
                    "state": "MD",
                    "zip": "123",
                    "country": "original country",
                    "committee_account_id": "735db943-9446-462a-9be0-c820baadb622",
                    "city": "new city",
                },
                "form_type": "SA15",
                "transaction_type_identifier": "OFFSET_TO_OPERATING_EXPENDITURES",
                "schema_name": "OFFSET_TO_OPERATING_EXPENDITURES",
                "fields_to_validate": ["contribution_amount"],
                "contribution_amount": 1,
                "contribution_date": "2021-01-01",
                "contributor_street_1": "original st",
                "contributor_state": "original state",
                "contributor_zip": "original zip",
                "contributor_organization_name": "original name",
                "contributor_city": "new city",
            },
            context={"request": self.mock_request},
        )
        valid_serializer.is_valid()
        valid_serializer.save()
        first_transaction = Transaction.objects.get(
            id="12345678-0000-0000-0000-9509df48e1aa"
        )
        self.assertEqual("new city", first_transaction.schedule_a.contributor_city)
        third_transaction = Transaction.objects.get(
            id="33333333-0000-0000-0000-9509df48e1aa"
        )
        self.assertEqual("new city", third_transaction.schedule_a.contributor_city)

    def test_itemization_inheritance(self):

        # Get tier 1 and test children and grandchildren
        tier1 = Transaction.objects.get(id="aaaaabbb-3274-47d8-9388-7294a3fd4321")
        tier2 = Transaction.objects.get(id="cccccbbb-3274-47d8-9388-7294a3fd4321")
        tier3 = Transaction.objects.get(id="77777bbb-3274-47d8-9388-7294a3fd4321")
        self.assertEquals(tier1.itemized, True)
        self.assertEquals(tier2.itemized, False)
        self.assertEquals(tier3.itemized, False)

        representation = TransactionSerializerBase().to_representation(tier2)
        self.assertEquals(representation["itemized"], True)

        representation = TransactionSerializerBase().to_representation(tier3)
        self.assertEquals(representation["itemized"], True)
