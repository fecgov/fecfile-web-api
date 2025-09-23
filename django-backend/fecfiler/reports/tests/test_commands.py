from django.core.management import call_command
from django.test import TestCase
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.web_services.summary.tasks import CalculationState
from django.core.management.base import CommandError


class CommandTest(TestCase):
    def setUp(self):
        self.missing_type_transaction = {}
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.f3x_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})

    def test_reset_summary_calculation_state_command(self):
        self.f3x_report.calculation_status = CalculationState.CALCULATING
        self.f3x_report.save()

        call_command(
            "reset_summary_calculation_state",
            "--report_id",
            str(self.f3x_report.id),
        )
        self.f3x_report.refresh_from_db()
        self.assertEqual(self.f3x_report.calculation_status, None)

    def test_missing_report_id_raises_error(self):
        with self.assertRaises(CommandError) as cm:
            call_command("reset_summary_calculation_state")

        self.assertIn(
            "the following arguments are required: --report_id", str(cm.exception)
        )
