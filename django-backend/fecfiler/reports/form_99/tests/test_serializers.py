from django.test import TestCase

from fecfiler.reports.form_99.models import Form99
from ..serializers import (
    Form99Serializer,
)
from fecfiler.authentication.models import Account
from rest_framework.request import Request, HttpRequest


class F99SerializerTestCase(TestCase):
    fixtures = ["test_committee_accounts"]

    def setUp(self):
        self.valid_f99_report = {
            "form_type": "F99N",
            "treasurer_last_name": "Testerson",
            "treasurer_first_name": "George",
            "date_signed": "2023-11-1",
            "street_1": "22 Test Street",
            "street_2": "Unit B",
            "city": "Testopolis",
            "state": "AL",
            "zip": "12345",
            "text_code": "MSM",
            "fields_to_validate": [f.name for f in Form99._meta.get_fields()],
        }

        self.invalid_f99_report = {
            "street_1": "22 Test Street",
            "street_2": "Unit B",
            "city": "Testopolis",
            "state": "TOO MANY CHARS",
            "text_code": "B",
            "fields_to_validate": [f.name for f in Form99._meta.get_fields()],
        }

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C00277616"
        self.mock_request.user = user

    def test_serializer_validate(self):
        valid_serializer = Form99Serializer(
            data=self.valid_f99_report,
            context={
                "request": self.mock_request,
            },
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = Form99Serializer(
            data=self.invalid_f99_report,
            context={
                "request": self.mock_request,
            },
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["state"])
        self.assertIsNotNone(invalid_serializer.errors["text_code"])
