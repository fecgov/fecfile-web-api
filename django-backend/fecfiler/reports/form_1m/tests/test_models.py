from django.test import TestCase
from ..models import Form1M
import datetime


class F1MTestCase(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.valid_form_1m = Form1M(
            committee_type="X",
            affiliated_date_form_f1_filed="2023-11-7",
        )

    def test_save_and_delete(self):
        self.valid_form_1m.save()
        form_1m_from_db = Form1M.objects.get(committee_type="X")
        self.assertIsInstance(form_1m_from_db, Form1M)
        self.assertEquals(
            form_1m_from_db.affiliated_date_form_f1_filed, datetime.date(2023, 11, 7)
        )
        form_1m_from_db.delete()
        self.assertRaises(
            Form1M.DoesNotExist,
            Form1M.objects.get,
            committee_type="X",
        )
