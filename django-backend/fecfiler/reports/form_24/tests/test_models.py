from django.test import TestCase
from ..models import Form24
import datetime


class F24TestCase(TestCase):
    fixtures = ["test_committee_accounts"]

    def setUp(self):
        self.valid_form_24 = Form24(
            street_1="22 Test Street",
            street_2="Unit B",
            city="Testopolis",
            state="AL",
            zip="12345",
            report_type_24_48="24",
            original_amendment_date="2023-11-01",
        )

    def test_save_and_delete(self):
        self.valid_form_24.save()
        form_24_from_db = Form24.objects.get(
            street_1="22 Test Street"
        )
        self.assertIsInstance(form_24_from_db, Form24)
        self.assertEquals(
            form_24_from_db.original_amendment_date,
            datetime.date(2023, 11, 1)
        )
        form_24_from_db.delete()
        self.assertRaises(
            Form24.DoesNotExist,
            Form24.objects.get,
            street_1="22 Test Street"
        )
