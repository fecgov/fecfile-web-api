from django.test import TestCase
from ..serializers import (
    Form3XSerializer,
    COVERAGE_DATE_REPORT_CODE_COLLISION,
)
from fecfiler.user.models import User
from fecfiler.reports.models import Report
from rest_framework.request import Request, HttpRequest
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.web_services.models import (
    FECStatus,
    FECSubmissionState,
    UploadSubmission,
)


class F3XSerializerTestCase(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.valid_f3x_report = {
            "form_type": "F3XN",
            "treasurer_last_name": "Validlastname",
            "treasurer_first_name": "Validfirstname",
            "coverage_from_date": "2023-01-01",
            "coverage_through_date": "2023-01-01",
            "report_code": "Q1",
            "date_signed": "2022-01-01",
            "upload_submission": {"fec_status": " ACCEPTED"},
        }

        self.invalid_f3x_report = {
            "form_type": "invalidformtype",
            "treasurer_last_name": "Validlastname",
            "date_signed": "2022-01-01",
        }

        self.mock_request = Request(HttpRequest())
        self.mock_request.user = User.objects.get(
            id="12345678-aaaa-bbbb-cccc-111122223333"
        )
        self.mock_request.session = {
            "committee_uuid": "11111111-2222-3333-4444-555555555555",
            "committee_id": "C01234567",
        }

    def test_serializer_validate(self):
        valid_serializer = Form3XSerializer(
            data=self.valid_f3x_report,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = Form3XSerializer(
            data=self.invalid_f3x_report,
            context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
        self.assertIsNotNone(invalid_serializer.errors["treasurer_first_name"])

    def test_used_report_code(self):
        valid_serializer = Form3XSerializer(
            data=self.valid_f3x_report,
            context={"request": self.mock_request},
        )
        valid_serializer.is_valid()
        valid_serializer.save()
        valid_serializer = Form3XSerializer(
            data=self.valid_f3x_report,
            context={"request": self.mock_request},
        )
        valid_serializer.is_valid()
        self.assertRaises(
            type(COVERAGE_DATE_REPORT_CODE_COLLISION), valid_serializer.save
        )

    def test_get_status_mapping(self):
        valid_serializer = Form3XSerializer(
            data=self.valid_f3x_report,
            context={"request": self.mock_request},
        )
        f3x_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        # retrieve from manager to populate annotations
        f3x_report = Report.objects.get(id=f3x_report.id)
        valid_serializer.is_valid()
        representation = valid_serializer.to_representation(f3x_report)
        self.assertEquals(representation["report_status"], "In progress")

        # .fec has been submitted but a result is pending
        f3x_report.upload_submission = UploadSubmission.objects.initiate_submission(
            f3x_report.id
        )
        # retrieve from manager to populate annotations
        f3x_report = Report.objects.get(id=f3x_report.id)
        representation = valid_serializer.to_representation(f3x_report)
        self.assertEquals(representation["report_status"], "Submission pending")

        # .fec was submitted and efo came back with an 'Accepted'
        f3x_report.upload_submission.fec_status = FECStatus.ACCEPTED
        f3x_report.upload_submission.save()
        # retrieve from manager to populate annotations
        f3x_report = Report.objects.get(id=f3x_report.id)
        representation = valid_serializer.to_representation(f3x_report)
        self.assertEquals(representation["report_status"], "Submission success")

        # an error occured at some point on our side after the user submitted
        f3x_report.upload_submission.fecfile_task_state = FECSubmissionState.FAILED
        f3x_report.upload_submission.fec_status = None
        f3x_report.upload_submission.save()
        # retrieve from manager to populate annotations
        f3x_report = Report.objects.get(id=f3x_report.id)
        representation = valid_serializer.to_representation(f3x_report)
        self.assertEquals(representation["report_status"], "Submission failure")

        # .fec was submitted and efo came back with a 'rejected'
        f3x_report.upload_submission.fecfile_task_state = FECSubmissionState.SUBMITTING
        f3x_report.upload_submission.fec_status = FECStatus.REJECTED
        f3x_report.upload_submission.save()
        # retrieve from manager to populate annotations
        f3x_report = Report.objects.get(id=f3x_report.id)
        representation = valid_serializer.to_representation(f3x_report)
        self.assertEquals(representation["report_status"], "Submission failure")
