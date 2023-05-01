from django.test import TestCase
from .models import F3XSummary
from datetime import datetime


class F3XTestCase(TestCase):
    fixtures = ["test_committee_accounts", "test_f3x_summaries"]

    def setUp(self):
        self.valid_f3x_summary = F3XSummary(
            form_type="F3XN",
            treasurer_last_name="Validlastname",
            treasurer_first_name="Validfirstname",
            date_signed="2022-01-01",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
        )

    def test_get_f3x_summary(self):
        f3x_summary = F3XSummary.objects.get(L6a_year_for_above_ytd="2005")
        self.assertEquals(f3x_summary.form_type, "F3XN")

    def test_save_and_delete(self):
        self.valid_f3x_summary.save()
        f3x_summary_from_db = F3XSummary.objects.get(date_signed="2022-01-01")
        self.assertIsInstance(f3x_summary_from_db, F3XSummary)
        self.assertEquals(f3x_summary_from_db.date_signed, datetime.date("2022-01-01"))
        f3x_summary_from_db.delete()
        self.assertRaises(
            F3XSummary.DoesNotExist,
            F3XSummary.objects.get,
            date_signed="2022-01-01",
        )

        soft_deleted_f3x_summary = F3XSummary.all_objects.get(date_signed="2022-01-01")
        self.assertEquals(
            soft_deleted_f3x_summary.date_signed, datetime.date("2022-01-01")
        )
        self.assertIsNotNone(soft_deleted_f3x_summary.deleted)
        soft_deleted_f3x_summary.hard_delete()
        self.assertRaises(
            F3XSummary.DoesNotExist,
            F3XSummary.all_objects.get,
            date_signed="2022-01-01",
        )
