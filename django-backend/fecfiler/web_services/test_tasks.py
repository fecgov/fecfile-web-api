from datetime import date
from django.test import TestCase
from .tasks import serialize_field, serialize_f3x_summary
from ..f3x_summaries.models import F3XSummary


class TasksTestCase(TestCase):
    fixtures = ["test_committee_accounts", "test_f3x_summaries"]

    def setUp(self):
        self.f3x = F3XSummary.objects.filter(id=9999).first()

    def test_serialize_field(self):
        serialized_text = serialize_field(self.f3x, "treasurer_last_name", F3XSummary)
        self.assertEquals(serialized_text, "Lastname")
        serialized_text_undefined = serialize_field(
            F3XSummary(), "treasurer_last_name", F3XSummary
        )
        self.assertEquals(serialized_text_undefined, "")
        serialized_amount = serialize_field(
            self.f3x, "L6b_cash_on_hand_beginning_period", F3XSummary
        )
        self.assertEqual(serialized_amount, "6")
        serialized_amount_undefined = serialize_field(
            F3XSummary(), "L6b_cash_on_hand_beginning_period", F3XSummary
        )
        self.assertEqual(serialized_amount_undefined, "")
        serialzed_date = serialize_field(self.f3x, "date_signed", F3XSummary)
        self.assertEqual(serialzed_date, "20040729")
        serialzed_date_undefined = serialize_field(
            F3XSummary(), "date_signed", F3XSummary
        )
        self.assertEqual(serialzed_date_undefined, "")
        serialized_boolean_true = serialize_field(
            self.f3x, "change_of_address", F3XSummary
        )
        self.assertEqual(serialized_boolean_true, "X")
        serialized_boolean_false = serialize_field(
            self.f3x, "qualified_committee", F3XSummary
        )
        self.assertEqual(serialized_boolean_false, "")
        serialized_boolean_undefined = serialize_field(
            F3XSummary(), "qualified_committee", F3XSummary
        )
        self.assertEqual(serialized_boolean_undefined, "")

    def test_serialize_f3x_summary(self):
        summary_row = serialize_f3x_summary(9999)
        split_row = summary_row.split(",")
        self.assertEqual(split_row[0], "F3XN")
        self.assertEqual(split_row[21], "20040729")
        self.assertEqual(split_row[3], "X")
        self.assertEqual(split_row[122], "381")
