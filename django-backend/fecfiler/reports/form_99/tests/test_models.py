from django.test import TestCase
from ..models import Form1M
import datetime
from decimal import Decimal


class F1MTestCase(TestCase):
    fixtures = ["test_committee_accounts"]

    def setUp(self):
        self.valid_form_1m = Form1M(
            street_1 = "22 Test Street",
            street_2 = "Unit B",
            city = "Testopolis",
            state = "AL",
            zip = "12345",
            committee_type = "X",
            affiliated_date_form_f1_filed = "2023-11-7",
            affiliated_committee_fec_id = "C00277616",
            affiliated_committee_name = "United Testing Committee"
        )

    def test_save_and_delete(self):
        self.valid_form_1m.save()
        form_1m_from_db = Form1M.objects.get(
            affiliated_committee_name="United Testing Committee"
        )
        self.assertIsInstance(form_1m_from_db, Form1M)
        self.assertEquals(
            form_1m_from_db.affiliated_date_form_f1_filed,
            datetime.date(2023, 11, 7)
        )
        form_1m_from_db.delete()
        self.assertRaises(
            Form1M.DoesNotExist,
            Form1M.objects.get,
            affiliated_committee_name="United Testing Committee",
        )
