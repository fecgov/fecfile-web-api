from django.test import TestCase

from fecfiler.reports.form_24.models import Form24
from ..serializers import (
    Form24Serializer,
)
from fecfiler.authentication.models import Account
from rest_framework.request import Request, HttpRequest


class F24SerializerTestCase(TestCase):
    fixtures = ["test_committee_accounts"]

    def setUp(self):
        self.valid_f24_report = {
            "form_type": "F24N",
            "treasurer_last_name": "Testerson",
            "treasurer_first_name": "George",
            "date_signed": "2023-11-1",
            "street_1": "22 Test Street",
            "street_2": "Unit B",
            "city": "Testopolis",
            "state": "AL",
            "zip": "12345",
            "report_type_24_48": "48",
            "original_amendment_date": "2023-11-01",
            "fields_to_validate": [f.name for f in Form24._meta.get_fields()],
        }

        self.invalid_f24_report = {
            "street_1": "22 Test Street",
            "street_2": "Unit B",
            "city": "Testopolis",
            "state": "AL",
            "report_type_24_48": "90c",
            "committee_type": "WAY TOO MANY CHARS",
        }

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C00277616"
        self.mock_request.user = user

    def test_serializer_validate(self):
        valid_serializer = Form24Serializer(
            data=self.valid_f24_report,
            context={
                "request": self.mock_request,
            },
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = Form24Serializer(
            data=self.invalid_f24_report,
            context={
                "request": self.mock_request,
            },
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["zip"])
        self.assertIsNotNone(invalid_serializer.errors["report_type_24_48"])
