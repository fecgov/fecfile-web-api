from django.test import TestCase
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.web_services.summary.tasks import CalculationState
from fecfiler.web_services.models import (
    DotFEC,
    UploadSubmission,
    WebPrintSubmission,
)
from ..utils.report_utils import reset_submitting_report
from django.core.management import call_command
from django.core.management.base import CommandError
from uuid import uuid4
import structlog

logger = structlog.get_logger(__name__)


class ReportUtilTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.f3x = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})

    def test_reset_submitting_report(self, use="method"):
        # create mock calculation bits
        self.f3x.calculation_token = uuid4()  # mock token
        self.f3x.calculation_status = CalculationState.CALCULATING

        # create mock dot fec record
        test_dot_fec_record = DotFEC.objects.create(
            report=self.f3x, file_name="testfile.txt"
        )

        # create mock upload submission
        test_upload_submission = UploadSubmission.objects.create(
            dot_fec=test_dot_fec_record
        )
        self.f3x.upload_submission = test_upload_submission

        # create mock webprint submission
        test_webprint_submission = WebPrintSubmission.objects.create(
            dot_fec=test_dot_fec_record,
        )
        self.f3x.webprint_submission = test_webprint_submission

        # save the report with all the mock data
        self.f3x.save()

        # reset the submitting report, either with the method or command
        if use == "command":
            call_command(
                "reset_submitting_report",
                "--report_id",
                str(self.f3x.id),
            )
        else:
            reset_submitting_report(str(self.f3x.id))

        # refresh from db and validate reset report submission
        self.f3x.refresh_from_db()
        self.assertEqual(self.f3x.calculation_token, None)
        self.assertEqual(self.f3x.calculation_status, None)
        self.assertEqual(self.f3x.upload_submission_id, None)
        self.assertEqual(self.f3x.webprint_submission_id, None)

        # validate dot fec record deleted
        with self.assertRaises(DotFEC.DoesNotExist):
            DotFEC.objects.get(report_id=self.f3x.id)

    def test_reset_submitting_report_command(self):
        self.test_reset_submitting_report(use="command")

    def test_reset_submitting_report_command_missing_arg(self):
        with self.assertRaises(CommandError) as cm:
            call_command("reset_submitting_report")

        self.assertIn(
            "the following arguments are required: --report_id", str(cm.exception)
        )
