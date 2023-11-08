from django.test import TestCase
from ..models import Form99
import datetime
from decimal import Decimal


class F99TestCase(TestCase):
    fixtures = ["test_committee_accounts"]

    def setUp(self):
        self.valid_form_99 = Form99(
            street_1 = "22 Test Street",
            street_2 = "Unit B",
            city = "Testopolis",
            state = "AL",
            zip = "12345",
            text_code = "MSM",
        )

    def test_save_and_delete(self):
        self.valid_form_99.save()
        form_99_from_db = Form99.objects.get(
            text_code="MSM"
        )
        self.assertIsInstance(form_99_from_db, Form99)
        self.assertEquals(
            form_99_from_db.text_code,
            "MSM"
        )
        form_99_from_db.delete()
        self.assertRaises(
            Form99.DoesNotExist,
            Form99.objects.get,
            text_code="MSM"
        )
