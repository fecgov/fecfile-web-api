from django.test import TestCase
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.web_services.summary.tasks import CalculationState
from ..utils.report_utils import reset_summary_calculation_state
import structlog

logger = structlog.get_logger(__name__)


class ReportUtilTestCase(TestCase):

    def setUp(self):
        self.missing_type_transaction = {}
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.f3x_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})

    def test_reset_calculation_status(self):
        self.f3x_report.calculation_status = CalculationState.CALCULATING
        self.f3x_report.save()
        reset_summary_calculation_state(str(self.f3x_report.id))
        self.f3x_report.refresh_from_db()
        self.assertEqual(self.f3x_report.calculation_status, None)
