from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import F3XSummary


class F3XTestCase(TestCase):
    fixtures = ['test_f3x_summaries']

    def setUp(self):
        self.valid_f3x_summary = F3XSummary(
            form_type="F3XN",
            filer_committee_id_number="C00123456",
            treasurer_last_name="Validlastname",
            treasurer_first_name="Validfirstname",
            date_signed="20220101"
        )

        self.invalid_f3x_summary = F3XSummary(
            form_type="invalidformtype",
            treasurer_last_name=1,
            treasurer_first_name="",
            date_signed="abcdefgh"
        )

    def test_get_f3x_summary(self):
        f3x_summary = F3XSummary.objects.get(treasurer_last_name="Lastname")
        self.assertEquals(f3x_summary.form_type, "F3XN")

    def test_full_clean(self):
        self.valid_f3x_summary.full_clean()
        self.assertRaises(ValidationError, self.invalid_f3x_summary.full_clean)

    def test_save_and_delete(self):
        self.valid_f3x_summary.save()
        f3x_summary_from_db = F3XSummary.objects.get(filer_committee_id_number="C00123456")
        self.assertIsInstance(f3x_summary_from_db, F3XSummary)
        self.assertEquals(f3x_summary_from_db.filer_committee_id_number, "C00123456")
        f3x_summary_from_db.delete()
        self.assertRaises(
            F3XSummary.DoesNotExist,
            F3XSummary.objects.get,
            filer_committee_id_number="C00123456"
        )

        softDeletedF3XSummary = F3XSummary.all_objects.get(filer_committee_id_number="C00123456")
        self.assertEquals(softDeletedF3XSummary.filer_committee_id_number, "C00123456")
        self.assertIsNotNone(softDeletedF3XSummary.deleted)
        softDeletedF3XSummary.hard_delete()
        self.assertRaises(F3XSummary.DoesNotExist, F3XSummary.all_objects.get, filer_committee_id_number="C00123456")
