from django.test import TestCase
from .models import F3XSummary


class F3XTestCase(TestCase):
    fixtures = ["test_f3x_summaries"]

    def setUp(self):
        self.valid_f3x_summary = F3XSummary(
            form_type="F3XN",
            filer_committee_id_number="C00123456",
            treasurer_last_name="Validlastname",
            treasurer_first_name="Validfirstname",
            date_signed="20220101",
        )

    def test_get_f3x_summary(self):
        f3x_summary = F3XSummary.objects.get(treasurer_last_name="Lastname")
        self.assertEquals(f3x_summary.form_type, "F3XN")

    def test_save_and_delete(self):
        self.valid_f3x_summary.save()
        f3x_summary_from_db = F3XSummary.objects.get(
            filer_committee_id_number="C00123456"
        )
        self.assertIsInstance(f3x_summary_from_db, F3XSummary)
        self.assertEquals(f3x_summary_from_db.filer_committee_id_number, "C00123456")
        f3x_summary_from_db.delete()
        self.assertRaises(
            F3XSummary.DoesNotExist,
            F3XSummary.objects.get,
            filer_committee_id_number="C00123456",
        )

        soft_deleted_f3x_summary = F3XSummary.all_objects.get(
            filer_committee_id_number="C00123456"
        )
        self.assertEquals(
            soft_deleted_f3x_summary.filer_committee_id_number, "C00123456"
        )
        self.assertIsNotNone(soft_deleted_f3x_summary.deleted)
        soft_deleted_f3x_summary.hard_delete()
        self.assertRaises(
            F3XSummary.DoesNotExist,
            F3XSummary.all_objects.get,
            filer_committee_id_number="C00123456",
        )
