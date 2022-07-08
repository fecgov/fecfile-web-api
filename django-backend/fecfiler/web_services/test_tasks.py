from django.test import TestCase
from .tasks import serialize_f3x_summary
from ..f3x_summaries.models import F3XSummary


class TasksTestCase(TestCase):
    fixtures = ["test_committee_accounts", "test_f3x_summaries"]

    def setUp(self):
        self.f3x = F3XSummary.objects.filter(id=9999).first()

    def test_serialize_f3x_summary(self):
        summary_row = serialize_f3x_summary(9999)
        split_row = summary_row.split(",")
        self.assertEqual(split_row[0], "F3XN")
        self.assertEqual(split_row[21], "20040729")
        self.assertEqual(split_row[3], "X")
        self.assertEqual(split_row[122], "381")
