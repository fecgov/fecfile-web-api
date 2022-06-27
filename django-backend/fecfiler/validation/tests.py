from django.test import TestCase
from .serializers import FecSchemaValidatorSerializerMixin
from django.http import QueryDict
from rest_framework.request import Request, HttpRequest


class MockF3XSerializerClass(FecSchemaValidatorSerializerMixin):
    schema_name = "F3X"

    def to_internal_value(self, data):
        return data


class FecSchemaValidatorSerializerMixin(TestCase):
    def setUp(self):
        self.valid_f3x_summary = {
            "form_type": "F3XN",
            "filer_committee_id_number": "C00123456",
            "treasurer_last_name": "Validlastname",
            "treasurer_first_name": "Validfirstname",
            "date_signed": "2022-01-01",
        }

        self.invalid_f3x_summary = {
            "form_type": "invalidformtype",
            "treasurer_last_name": "Validlastname",
        }

    def test_serializer_validate(self):
        valid_serializer = MockF3XSerializerClass(
            data=self.valid_f3x_summary,
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = MockF3XSerializerClass(
            data=self.invalid_f3x_summary,
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
        self.assertIsNotNone(invalid_serializer.errors["treasurer_first_name"])
        self.assertIsNotNone(invalid_serializer.errors["date_signed"])

    def test_serializer_partial_validate(self):
        partial_validate_request = HttpRequest()
        partial_validate_request.GET = QueryDict(
            "fields_to_validate=treasurer_last_name"
        )
        """ Notice that we are putting `invalid_f3x_summery in here`
        This serializer will come out valid because the request asks
        to ONLY validate `treasurer_first_name`
        """
        valid_serializer = MockF3XSerializerClass(
            data=self.invalid_f3x_summary,
            context={"request": Request(partial_validate_request)},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        """ Now, we ask to validate a field that we have given a bad value
        This serailizer should fail
        """
        partial_validate_request_invalid = HttpRequest()
        partial_validate_request_invalid.GET = QueryDict("fields_to_validate=form_type")
        invalid_serializer = MockF3XSerializerClass(
            data=self.invalid_f3x_summary,
            context={"request": Request(partial_validate_request_invalid)},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
