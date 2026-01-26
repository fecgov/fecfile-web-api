from django.test import TestCase
from ..serializers import (
    Form3XSerializer,
    COVERAGE_DATE_REPORT_CODE_COLLISION,
    COVERAGE_DATES_EXCLUDE_EXISTING_TRANSACTIONS,
)
from fecfiler.user.models import User
from fecfiler.reports.models import Report
from rest_framework.request import Request, HttpRequest
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.tests.utils import create_schedule_a
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.web_services.models import (
    FECStatus,
    FECSubmissionState,
    UploadSubmission,
)
from fecfiler.reports.managers import (
    REPORT_STATUS_MAP,
    STATUS_CODE_IN_PROGRESS,
    STATUS_CODE_SUCCESS,
    STATUS_CODE_PENDING,
    STATUS_CODE_FAILED,
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
        self.assertEqual(
            representation["report_status"],
            REPORT_STATUS_MAP.get(STATUS_CODE_IN_PROGRESS),
        )

        # .fec has been submitted but a result is pending
        f3x_report.upload_submission = UploadSubmission.objects.initiate_submission(
            f3x_report.id
        )
        # retrieve from manager to populate annotations
        f3x_report = Report.objects.get(id=f3x_report.id)
        representation = valid_serializer.to_representation(f3x_report)
        self.assertEqual(
            representation["report_status"], REPORT_STATUS_MAP.get(STATUS_CODE_PENDING)
        )

        # .fec was submitted and efo came back with an 'Accepted'
        f3x_report.upload_submission.fec_status = FECStatus.ACCEPTED
        f3x_report.upload_submission.save()
        # retrieve from manager to populate annotations
        f3x_report = Report.objects.get(id=f3x_report.id)
        representation = valid_serializer.to_representation(f3x_report)
        self.assertEqual(
            representation["report_status"], REPORT_STATUS_MAP.get(STATUS_CODE_SUCCESS)
        )

        # an error occured at some point on our side after the user submitted
        f3x_report.upload_submission.fecfile_task_state = FECSubmissionState.FAILED
        f3x_report.upload_submission.fec_status = None
        f3x_report.upload_submission.save()
        # retrieve from manager to populate annotations
        f3x_report = Report.objects.get(id=f3x_report.id)
        representation = valid_serializer.to_representation(f3x_report)
        self.assertEqual(
            representation["report_status"], REPORT_STATUS_MAP.get(STATUS_CODE_FAILED)
        )

        # .fec was submitted and efo came back with a 'rejected'
        f3x_report.upload_submission.fecfile_task_state = FECSubmissionState.SUBMITTING
        f3x_report.upload_submission.fec_status = FECStatus.REJECTED
        f3x_report.upload_submission.save()
        # retrieve from manager to populate annotations
        f3x_report = Report.objects.get(id=f3x_report.id)
        representation = valid_serializer.to_representation(f3x_report)
        self.assertEqual(
            representation["report_status"], REPORT_STATUS_MAP.get(STATUS_CODE_FAILED)
        )

    def test_update_coverage_to_overlapping_dates(self):
        report_a = create_form3x(self.committee, "2024-01-01", "2024-03-31")
        create_form3x(self.committee, "2024-04-01", "2024-06-30")

        serializer = Form3XSerializer(
            data=self.valid_f3x_report,
            context={"request": self.mock_request},
        )
        serializer.is_valid()
        self.assertRaises(
            type(COVERAGE_DATE_REPORT_CODE_COLLISION),
            serializer.update,
            report_a,
            {"coverage_from_date": "2024-01-01", "coverage_through_date": "2024-05-31"},
        )

    def test_update_coverage_to_exclude_transaction(self):
        report_a = create_form3x(self.committee, "2024-01-01", "2024-03-31")
        create_schedule_a(
            "INDIVIDUAL_RECEIPT", self.committee, None, "2024-03-31", 250, report=report_a
        )

        serializer = Form3XSerializer(
            data=self.valid_f3x_report,
            context={"request": self.mock_request},
        )
        serializer.is_valid()
        self.assertRaises(
            type(COVERAGE_DATES_EXCLUDE_EXISTING_TRANSACTIONS),
            serializer.update,
            report_a,
            {"coverage_from_date": "2024-01-01", "coverage_through_date": "2024-02-28"},
        )

    def test_update_coverage_to_exclude_memo_transaction(self):
        report_a = create_form3x(self.committee, "2024-01-01", "2024-03-31")
        create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            None,
            "2024-03-31",
            250,
            report=report_a,
            memo_code=True,
        )

        serializer = Form3XSerializer(
            data=self.valid_f3x_report,
            context={"request": self.mock_request},
        )
        serializer.is_valid()
        self.assertEqual(
            serializer.update(
                report_a,
                {
                    "coverage_from_date": "2024-01-01",
                    "coverage_through_date": "2024-02-28",
                },
            ),
            report_a,
        )

    def test_update_coverage_to_exclude_deleted_transaction(self):
        report_a = create_form3x(self.committee, "2024-01-01", "2024-03-31")
        transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            None,
            "2024-03-31",
            250,
            report=report_a,
            memo_code=False,
        )
        transaction.delete()

        serializer = Form3XSerializer(
            data=self.valid_f3x_report,
            context={"request": self.mock_request},
        )
        serializer.is_valid()
        self.assertEqual(
            serializer.update(
                report_a,
                {
                    "coverage_from_date": "2024-01-01",
                    "coverage_through_date": "2024-02-28",
                },
            ),
            report_a,
        )
