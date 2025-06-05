from django.test import TestCase
from ..models import Form99


class F99TestCase(TestCase):
    def setUp(self):
        self.valid_form_99 = Form99(
            text_code="MSM",
        )

    def test_save_and_delete(self):
        self.valid_form_99.save()
        form_99_from_db = Form99.objects.get(text_code="MSM")
        self.assertIsInstance(form_99_from_db, Form99)
        self.assertEqual(form_99_from_db.text_code, "MSM")
        form_99_from_db.delete()
        self.assertRaises(Form99.DoesNotExist, Form99.objects.get, text_code="MSM")
