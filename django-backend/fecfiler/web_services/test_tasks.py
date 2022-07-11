from django.test import TestCase
from .tasks import serialize_f3x_summary, serialize_transaction
from fecfiler.f3x_summaries.models import F3XSummary
from fecfiler.scha_transactions.models import SchATransaction


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
        split_row = summary_row.split(",")
        self.assertEqual(split_row[0], "F3XN")
        self.assertEqual(split_row[21], "20040729")
        self.assertEqual(split_row[3], "X")
        self.assertEqual(split_row[122], "381")

        with self.assertRaisesMessage(Exception, "report: 100000000 not found"):
            serialize_f3x_summary(100000000)

    def test_serialize_transaction(self):
        transaction_row = serialize_transaction(9999)
        split_row = transaction_row.split(",")
        self.assertEqual(split_row[0], "SA11AI")
        self.assertEqual(split_row[20], "20200419")
        self.assertEqual(split_row[42], "X")
        self.assertEqual(split_row[21], "1234")

        with self.assertRaisesMessage(Exception, "transaction: 100000000 not found"):
            serialize_transaction(100000000)
