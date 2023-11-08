from django.test import TestCase
from ..serializers import (
    Form1MSerializer,
)
from fecfiler.authentication.models import Account
from rest_framework.request import Request, HttpRequest


class F1MSerializerTestCase(TestCase):
    fixtures = ["test_committee_accounts"]

    def setUp(self):
        self.valid_f1m_report = {
            "form_type": "F1MN",
            "treasurer_last_name": "Testerson",
            "treasurer_first_name": "George",
            "committee_name": "Testing Committee",
            "date_signed": "2023-11-1",
            "street_1": "22 Test Street",
            "street_2": "Unit B",
            "city": "Testopolis",
            "state": "AL",
            "zip": "12345",
            "committee_type": "X",
            "affiliated_date_form_f1_filed": "2023-11-7",
            "affiliated_committee_fec_id": "C00277616",
            "affiliated_committee_name": "United Testing Committee"
        }

        self.invalid_f1m_report = {
            "street_1": "22 Test Street",
            "street_2": "Unit B",
            "city": "Testopolis",
            "state": "AL",
            "committee_type": "WAY TOO MANY CHARS",
        }

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C00277616"
        self.mock_request.user = user

    def test_serializer_validate(self):
        valid_serializer = Form1MSerializer(
            data=self.valid_f1m_report,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = Form1MSerializer(
            data=self.invalid_f1m_report,
            context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["zip"])
        self.assertIsNotNone(invalid_serializer.errors["committee_type"])
