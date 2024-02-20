from django.test import TestCase

from fecfiler.reports.form_99.models import Form99
from ..serializers import (
    Form99Serializer,
)
from fecfiler.user.models import User
from rest_framework.request import Request, HttpRequest


class F99SerializerTestCase(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.valid_f99_report = {
            "form_type": "F99N",
            "committee_name": "my committee",
            "treasurer_last_name": "Testerson",
            "treasurer_first_name": "George",
            "date_signed": "2023-11-1",
            "street_1": "22 Test Street",
            "street_2": "Unit B",
            "city": "Testopolis",
            "state": "AL",
            "zip": "12345",
            "text_code": "MSM",
            "message_text": "A message to FEC",
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
        self.mock_request.user = User.objects.get(
            id="12345678-aaaa-bbbb-cccc-111122223333"
        )
        self.mock_request.session = {
            "committee_uuid": "11111111-2222-3333-4444-555555555555"
        }

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
