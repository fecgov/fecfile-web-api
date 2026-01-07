from unittest.mock import patch
from django.test import TestCase
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.tests.utils import create_schedule_a
from fecfiler.contacts.tests.utils import create_test_individual_contact


class ReportDeleteAggregatesTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        self.contact = create_test_individual_contact(
            "last", "first", self.committee.id
        )
        # Create a simple Schedule A transaction attached to the report
        self.tx = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact,
            "2024-01-10",
            amount="100.00",
            report=self.report,
        )

    @patch(
        "fecfiler.transactions.aggregate_service."
        "update_aggregates_for_affected_transactions"
    )
    def test_delete_report_invokes_aggregate_service_for_transactions(
        self, mock_update
    ):
        # Delete the report; should delete attached transactions via instance delete
        self.report.delete()
        # Ensure aggregation service was invoked for at least one transaction
        self.assertGreaterEqual(mock_update.call_count, 1)
        # Validate one of the calls used the delete action
        called_actions = [args[1] for args, _ in mock_update.call_args_list]
        self.assertIn("delete", called_actions)
