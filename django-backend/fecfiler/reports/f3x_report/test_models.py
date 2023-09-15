from django.test import TestCase
from .models import F3XReport
import datetime


class F3XTestCase(TestCase):
    fixtures = ["test_committee_accounts", "test_f3x_reports"]

    def setUp(self):
        self.valid_f3x_report = F3XReport(
            form_type="F3XN",
            treasurer_last_name="Validlastname",
            treasurer_first_name="Validfirstname",
            date_signed="2022-01-01",
            committee_account_id="735db943-9446-462a-9be0-c820baadb622",
        )

    def test_get_f3x_report(self):
        f3x_report = F3XReport.objects.get(L6a_year_for_above_ytd="2005")
        self.assertEquals(f3x_report.form_type, "F3XN")

    def test_save_and_delete(self):
        self.valid_f3x_report.save()
        f3x_report_from_db = F3XReport.objects.get(date_signed="2022-01-01")
        self.assertIsInstance(f3x_report_from_db, F3XReport)
        self.assertEquals(f3x_report_from_db.date_signed, datetime.date(2022, 1, 1))
        f3x_report_from_db.delete()
        self.assertRaises(
            F3XReport.DoesNotExist,
            F3XReport.objects.get,
            date_signed="2022-01-01",
        )

        soft_deleted_f3x_report = F3XReport.all_objects.get(date_signed="2022-01-01")
        self.assertEquals(
            soft_deleted_f3x_report.date_signed, datetime.date(2022, 1, 1)
        )
        self.assertIsNotNone(soft_deleted_f3x_report.deleted)
        soft_deleted_f3x_report.hard_delete()
        self.assertRaises(
            F3XReport.DoesNotExist,
            F3XReport.all_objects.get,
            date_signed="2022-01-01",
        )
