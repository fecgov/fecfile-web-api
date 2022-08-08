from django.test import TestCase
from .tasks import (
    create_dot_fec_content,
    create_dot_fec,
    serialize_f3x_summary,
    serialize_transaction,
    serialize_transactions,
)
from .dot_fec_serializer import CRLF_STR
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

    def test_serialize_f3x_summary(self):
        summary_row = serialize_f3x_summary(9999)
        split_row = summary_row.split(chr(ascii.FS))
        self.assertEqual(split_row[0], "F3XN")
        self.assertEqual(split_row[21], "20040729")
        self.assertEqual(split_row[3], "X")
        self.assertEqual(split_row[122], "381.00")

        with self.assertRaisesMessage(Exception, "report: 100000000 not found"):
            serialize_f3x_summary(100000000)

    def test_serialize_transaction(self):
        transaction_row = serialize_transaction(self.transaction)
        split_row = transaction_row.split(chr(ascii.FS))
        self.assertEqual(split_row[0], "SA11AI")
        self.assertEqual(split_row[19], "20200419")
        self.assertEqual(split_row[42], "X")
        self.assertEqual(split_row[20], "1234.56")

        with self.assertRaisesMessage(Exception, "<class 'int'> is not a transaction"):
            serialize_transaction(123)

    def test_serialize_transactions(self):
        transactions = SchATransaction.objects.filter(id=9999)
        transaction_rows = serialize_transactions(transactions)
        split_row = transaction_rows[0].split(chr(ascii.FS))
        self.assertEqual(split_row[0], "SA11AI")
        self.assertEqual(split_row[19], "20200419")
        self.assertEqual(split_row[42], "X")
        self.assertEqual(split_row[20], "1234.56")

        no_transactions = SchATransaction.objects.filter(id=100000000)
        no_transaction_rows = serialize_transactions(no_transactions)
        self.assertEqual(no_transaction_rows, [])

    def test_create_dot_fec_content(self):
        file_content, file_name = create_dot_fec_content(9999)
        self.assertEqual(file_content.count(CRLF_STR), 2)
        self.assertEqual(file_name.split("_")[0], "9999")

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
