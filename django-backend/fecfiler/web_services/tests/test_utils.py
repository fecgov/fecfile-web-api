from django.test import TestCase
from django.core.management import call_command
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.web_services.models import (
    FECSubmissionState,
    UploadSubmission,
)
from ..utils.submission_utils import fail_open_submissions


class WebServicesUtilTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")

    def test_fail_open_submissions(self):
        # one report submission will be completed and should not be marked as failed
        f3x_completed = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        submission_completed = UploadSubmission.objects.initiate_submission(
            str(f3x_completed.id)
        )
        submission_completed.save_state(FECSubmissionState.SUCCEEDED)
        self.assertEqual(
            submission_completed.fecfile_task_state, FECSubmissionState.SUCCEEDED.value
        )

        # another report submission will be in-progress and should be marked as failed
        f3x_inprogress = create_form3x(self.committee, "2024-02-01", "2024-03-01", {})
        submission_inprogress = UploadSubmission.objects.initiate_submission(
            str(f3x_inprogress.id)
        )
        self.assertEqual(
            submission_inprogress.fecfile_task_state,
            FECSubmissionState.INITIALIZING.value,
        )

        # fail open submissions
        fail_open_submissions()

        # refresh from db and validate states
        submission_completed.refresh_from_db()
        submission_inprogress.refresh_from_db()
        self.assertEqual(
            submission_completed.fecfile_task_state, FECSubmissionState.SUCCEEDED.value
        )
        self.assertEqual(
            submission_inprogress.fecfile_task_state, FECSubmissionState.FAILED.value
        )
