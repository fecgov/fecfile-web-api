from django.test import TestCase
from ..serializers import (
    Form3XSerializer,
    COVERAGE_DATE_REPORT_CODE_COLLISION,
)
from fecfiler.user.models import User
from rest_framework.request import Request, HttpRequest


class F3XSerializerTestCase(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.valid_f3x_report = {
            "form_type": "F3XN",
            "treasurer_last_name": "Validlastname",
            "treasurer_first_name": "Validfirstname",
            "coverage_from_date": "2023-01-01",
            "coverage_through_date": "2023-01-01",
            "report_code": "Q1",
            "date_signed": "2022-01-01",
            "upload_submission": {"fec_status": " ACCEPTED"},
        }

        self.invalid_f3x_report = {
            "form_type": "invalidformtype",
            "treasurer_last_name": "Validlastname",
            "date_signed": "2022-01-01",
        }

        self.mock_request = Request(HttpRequest())
        self.mock_request.user = User.objects.get(
            id="12345678-aaaa-bbbb-cccc-111122223333"
        )
        self.mock_request.session = {
            "committee_uuid": "11111111-2222-3333-4444-555555555555"
        }

    def test_serializer_validate(self):
        valid_serializer = Form3XSerializer(
            data=self.valid_f3x_report,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = Form3XSerializer(
            data=self.invalid_f3x_report,
            context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
        self.assertIsNotNone(invalid_serializer.errors["treasurer_first_name"])

    def test_used_report_code(self):
        valid_serializer = Form3XSerializer(
            data=self.valid_f3x_report,
            context={"request": self.mock_request},
        )
        valid_serializer.is_valid()
        valid_serializer.save()
        valid_serializer = Form3XSerializer(
            data=self.valid_f3x_report,
            context={"request": self.mock_request},
        )
        valid_serializer.is_valid()
        self.assertRaises(
            type(COVERAGE_DATE_REPORT_CODE_COLLISION), valid_serializer.save
        )
