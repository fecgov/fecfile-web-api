from django.test import TestCase
from .serializers import F3XSummarySerializer


class F3XSerializerTestCase(TestCase):
    def setUp(self):
        self.valid_f3x_summary = {
            "form_type": "F3XN",
            "filer_committee_id_number": "C00123456",
            "treasurer_last_name": "Validlastname",
            "treasurer_first_name": "Validfirstname",
            "date_signed": "20220101",
        }

        self.invalid_f3x_summary = {
            "form_type": "invalidformtype",
            "treasurer_last_name": "Validlastname",
            "date_signed": "20220101",
        }

    def test_serializer_validate(self):
        valid_serializer = F3XSummarySerializer(data=self.valid_f3x_summary)
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = F3XSummarySerializer(data=self.invalid_f3x_summary)
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
        self.assertIsNotNone(invalid_serializer.errors["treasurer_first_name"])
