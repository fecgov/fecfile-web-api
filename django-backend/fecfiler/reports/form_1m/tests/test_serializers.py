from django.test import TestCase

from fecfiler.reports.form_1m.models import Form1M
from ..serializers import (
    Form1MSerializer,
)
from fecfiler.user.models import User
from rest_framework.request import Request, HttpRequest
from fecfiler.reports.form_1m.utils import add_form_1m_contact_fields


class F1MSerializerTestCase(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.valid_f1m_report = {
            "form_type": "F1MN",
            "committee_name": "committee name",
            "treasurer_last_name": "Testerson",
            "treasurer_first_name": "George",
            "date_signed": "2023-11-1",
            "street_1": "22 Test Street",
            "street_2": "Unit B",
            "city": "Testopolis",
            "state": "AL",
            "zip": "12345",
            "committee_type": "X",
            "affiliated_date_form_f1_filed": "2023-11-7",
            "affiliated_committee_fec_id": "C00277616",
            "affiliated_committee_name": "United Testing Committee",
            "fields_to_validate": [f.name for f in Form1M._meta.get_fields()],
        }

        self.invalid_f1m_report = {
            "street_1": "22 Test Street",
            "street_2": "Unit B",
            "city": "Testopolis",
            "state": "AL",
            "committee_type": "WAY TOO MANY CHARS",
        }

        self.mock_request = Request(HttpRequest())
        self.mock_request.user = User.objects.get(
            id="12345678-aaaa-bbbb-cccc-111122223333"
        )

    def test_serializer_validate(self):
        valid_serializer = Form1MSerializer(
            data=self.valid_f1m_report,
            context={
                "request": self.mock_request,
            },
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = Form1MSerializer(
            data=self.invalid_f1m_report,
            context={
                "request": self.mock_request,
            },
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["zip"])
        self.assertIsNotNone(invalid_serializer.errors["committee_type"])

    def test_serializer_utils_to_representation(self):
        data = dict(
            contact_affiliated=dict(
                committee_id="C000000009",
                name="Affiliated Committee",
            )
        )

        representation = dict(
            committee_name="Elect Person"
        )

        add_form_1m_contact_fields(data, representation)

        self.assertEquals(
            representation["affiliated_committee_name"], "Affiliated Committee"
        )
