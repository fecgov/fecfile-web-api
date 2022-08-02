from django.test import TestCase
from .tasks import create_dot_fec
from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.scha_transactions.models import SchATransaction
from curses import ascii
from pathlib import Path
from fecfiler.settings import CELERY_LOCAL_STORAGE_DIRECTORY


class TasksTestCase(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_individual_receipt",
    ]

    def setUp(self):
        self.f3x = F3XSummary.objects.filter(id=9999).first()
        self.transaction = SchATransaction.objects.filter(id=9999).first()

    def test_create_dot_fec(self):
        file_name = create_dot_fec(9999, True)
        result_dot_fec = Path(CELERY_LOCAL_STORAGE_DIRECTORY).joinpath(file_name)
        try:
            with open(result_dot_fec, encoding="utf-8") as f:
                lines = f.readlines()
                self.assertEqual(lines[0][:5], "F3XN" + chr(ascii.FS))
                self.assertEqual(lines[1][:7], "SA11AI" + chr(ascii.FS))
        finally:
            if result_dot_fec.exists():
                result_dot_fec.unlink()
