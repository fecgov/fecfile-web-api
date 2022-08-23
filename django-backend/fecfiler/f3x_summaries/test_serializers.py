from django.test import TestCase

from fecfiler.f3x_summaries.models import F3XSummary

from .serializers import F3XSummarySerializer
from fecfiler.authentication.models import Account
from rest_framework.request import Request, HttpRequest


class F3XSerializerTestCase(TestCase):
    fixtures = ["test_committee_accounts"]

    def setUp(self):
        self.valid_f3x_summary = {
            "form_type": "F3XN",
            "filer_committee_id_number": "C00123456",
            "treasurer_last_name": "Validlastname",
            "treasurer_first_name": "Validfirstname",
            "date_signed": "2022-01-01",
            "upload_submission": {
                "fec_status":" ACCEPTED"
            }
        }

        self.invalid_f3x_summary = {
            "form_type": "invalidformtype",
            "treasurer_last_name": "Validlastname",
            "date_signed": "2022-01-01",
        }

        self.mock_request = Request(HttpRequest())
        user = Account()
        user.cmtee_id = "C00277616"
        self.mock_request.user = user

    def test_serializer_validate(self):
        valid_serializer = F3XSummarySerializer(
            data=self.valid_f3x_summary,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = F3XSummarySerializer(
            data=self.invalid_f3x_summary,
            context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
        self.assertIsNotNone(invalid_serializer.errors["treasurer_first_name"])

    def test_get_submission_status(self):
        f3x_summary = {
            "form_type": "F3XN",
            "filer_committee_id_number": "C00123456",
            "treasurer_last_name": "Validlastname",
            "treasurer_first_name": "Validfirstname",
            "date_signed": "2022-01-01",
            "upload_submission": {
                "fec_status": "ACCEPTED"
            }
        }
        valid_serializer = F3XSummarySerializer(
            data=f3x_summary,
            context={"request": self.mock_request},
        )
        f3x_object = F3XSummary()
        self.assertEqual(valid_serializer.get_submission_status(f3x_object), None)
        f3x_object.submission_status = "In-Progress"
        self.assertEqual(
            valid_serializer.get_submission_status(f3x_object),
            'In-Progress'
        )
