from django.test import TestCase
from ..serializers import (
    Form3Serializer,
    COVERAGE_DATE_REPORT_CODE_COLLISION,
    COVERAGE_DATES_EXCLUDE_EXISTING_TRANSACTIONS,
)
from fecfiler.reports.form_3x.serializers import Form3XSerializer

from fecfiler.user.models import User
from fecfiler.reports.models import Report
from rest_framework.request import Request, HttpRequest
from fecfiler.reports.tests.utils import create_form3, create_form3x
from fecfiler.transactions.tests.utils import create_schedule_a, create_ie
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
from fecfiler.web_services.summary.tasks import CalculationState
from uuid import uuid4
from datetime import datetime


class F3SerializerTestCase(TestCase):
    fixtures = ["C01234567_user_and_committee"]

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.valid_f3_report = {
            "form_type": "F3N",
            "treasurer_last_name": "Validlastname",
            "treasurer_first_name": "Validfirstname",
            "coverage_from_date": "2023-01-01",
            "coverage_through_date": "2023-01-01",
            "report_code": "Q1",
            "date_signed": "2022-01-01",
            "upload_submission": {"fec_status": " ACCEPTED"},
        }

        self.invalid_f3_report = {
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
        valid_serializer = Form3Serializer(
            data=self.valid_f3_report,
            context={"request": self.mock_request},
        )
        self.assertTrue(valid_serializer.is_valid(raise_exception=True))
        invalid_serializer = Form3Serializer(
            data=self.invalid_f3_report,
            context={"request": self.mock_request},
        )
        self.assertFalse(invalid_serializer.is_valid())
        self.assertIsNotNone(invalid_serializer.errors["form_type"])
        self.assertIsNotNone(invalid_serializer.errors["treasurer_first_name"])

    def test_used_report_code(self):
        valid_serializer = Form3Serializer(
            data=self.valid_f3_report,
            context={"request": self.mock_request},
        )
        valid_serializer.is_valid(raise_exception=True)
        valid_serializer.save()
        valid_serializer = Form3Serializer(
            data=self.valid_f3_report,
            context={"request": self.mock_request},
        )
        valid_serializer.is_valid(raise_exception=True)
        self.assertRaises(
            type(COVERAGE_DATE_REPORT_CODE_COLLISION), valid_serializer.save
        )

    def test_get_status_mapping(self):
        valid_serializer = Form3Serializer(
            data=self.valid_f3_report,
            context={"request": self.mock_request},
        )
        f3_report = create_form3(self.committee, "2024-01-01", "2024-02-01", {})
        # retrieve from manager to populate annotations
        f3_report = Report.objects.get(id=f3_report.id)
        valid_serializer.is_valid(raise_exception=True)
        representation = valid_serializer.to_representation(f3_report)
        self.assertEqual(
            representation["report_status"],
            REPORT_STATUS_MAP.get(STATUS_CODE_IN_PROGRESS),
        )

        # .fec has been submitted but a result is pending
        f3_report.upload_submission = UploadSubmission.objects.initiate_submission(
            f3_report.id
        )
        # retrieve from manager to populate annotations
        f3_report = Report.objects.get(id=f3_report.id)
        representation = valid_serializer.to_representation(f3_report)
        self.assertEqual(
            representation["report_status"], REPORT_STATUS_MAP.get(STATUS_CODE_PENDING)
        )

        # .fec was submitted and efo came back with an 'Accepted'
        f3_report.upload_submission.fec_status = FECStatus.ACCEPTED
        f3_report.upload_submission.save()
        # retrieve from manager to populate annotations
        f3_report = Report.objects.get(id=f3_report.id)
        representation = valid_serializer.to_representation(f3_report)
        self.assertEqual(
            representation["report_status"], REPORT_STATUS_MAP.get(STATUS_CODE_SUCCESS)
        )

        # an error occured at some point on our side after the user submitted
        f3_report.upload_submission.fecfile_task_state = FECSubmissionState.FAILED
        f3_report.upload_submission.fec_status = None
        f3_report.upload_submission.save()
        # retrieve from manager to populate annotations
        f3_report = Report.objects.get(id=f3_report.id)
        representation = valid_serializer.to_representation(f3_report)
        self.assertEqual(
            representation["report_status"], REPORT_STATUS_MAP.get(STATUS_CODE_FAILED)
        )

        # .fec was submitted and efo came back with a 'rejected'
        f3_report.upload_submission.fecfile_task_state = FECSubmissionState.SUBMITTING
        f3_report.upload_submission.fec_status = FECStatus.REJECTED
        f3_report.upload_submission.save()
        # retrieve from manager to populate annotations
        f3_report = Report.objects.get(id=f3_report.id)
        representation = valid_serializer.to_representation(f3_report)
        self.assertEqual(
            representation["report_status"], REPORT_STATUS_MAP.get(STATUS_CODE_FAILED)
        )

    def test_update_coverage_to_overlapping_dates(self):
        report_a = create_form3(self.committee, "2024-01-01", "2024-03-31")
        create_form3(self.committee, "2024-04-01", "2024-06-30")

        serializer = Form3Serializer(
            data=self.valid_f3_report,
            context={"request": self.mock_request},
        )
        serializer.is_valid(raise_exception=True)
        self.assertRaises(
            type(COVERAGE_DATE_REPORT_CODE_COLLISION),
            serializer.update,
            report_a,
            {
                "coverage_from_date": datetime.strptime("2024-01-01", "%Y-%m-%d").date(),
                "coverage_through_date": datetime.strptime(
                    "2024-05-31", "%Y-%m-%d"
                ).date(),
            },
        )

    def test_update_coverage_to_exclude_transaction(self):
        report_a = create_form3(self.committee, "2024-01-01", "2024-03-31")
        create_schedule_a(
            "INDIVIDUAL_RECEIPT", self.committee, None, "2024-03-31", 250, report=report_a
        )

        serializer = Form3Serializer(
            data=self.valid_f3_report,
            context={"request": self.mock_request},
        )
        serializer.is_valid(raise_exception=True)
        self.assertRaises(
            type(COVERAGE_DATES_EXCLUDE_EXISTING_TRANSACTIONS),
            serializer.update,
            report_a,
            {
                "coverage_from_date": datetime.strptime("2024-01-01", "%Y-%m-%d").date(),
                "coverage_through_date": datetime.strptime(
                    "2024-02-28", "%Y-%m-%d"
                ).date(),
            },
        )

    def test_update_coverage_to_exclude_memo_transaction(self):
        report_a = create_form3(self.committee, "2024-01-01", "2024-03-31")
        create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            None,
            "2024-03-31",
            250,
            report=report_a,
            memo_code=True,
        )

        serializer = Form3Serializer(
            data=self.valid_f3_report,
            context={"request": self.mock_request},
        )
        serializer.is_valid(raise_exception=True)
        self.assertEqual(
            serializer.update(
                report_a,
                {
                    "coverage_from_date": datetime.strptime(
                        "2024-01-01", "%Y-%m-%d"
                    ).date(),
                    "coverage_through_date": datetime.strptime(
                        "2024-02-28", "%Y-%m-%d"
                    ).date(),
                },
            ),
            report_a,
        )

    def test_update_coverage_to_exclude_deleted_transaction(self):
        report_a = create_form3(self.committee, "2024-01-01", "2024-03-31")
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

        serializer = Form3Serializer(
            data=self.valid_f3_report,
            context={"request": self.mock_request},
        )
        serializer.is_valid(raise_exception=True)
        self.assertEqual(
            serializer.update(
                report_a,
                {
                    "coverage_from_date": datetime.strptime(
                        "2024-01-01", "%Y-%m-%d"
                    ).date(),
                    "coverage_through_date": datetime.strptime(
                        "2024-02-28", "%Y-%m-%d"
                    ).date(),
                },
            ),
            report_a,
        )

    def test_update_coverage_dates_marks_report_dirty(self):
        report = create_form3(self.committee, "2026-01-01", "2026-01-31")
        report.calculation_status = CalculationState.FAILED.value
        report.calculation_token = uuid4()
        report.save()

        serializer = Form3Serializer(
            data=self.valid_f3_report,
            context={"request": self.mock_request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.update(
            report,
            {
                "coverage_from_date": datetime.strptime("2025-01-01", "%Y-%m-%d").date(),
                "coverage_through_date": datetime.strptime(
                    "2025-01-31", "%Y-%m-%d"
                ).date(),
            },
        )

        report.refresh_from_db()
        self.assertIsNone(report.calculation_status)
        self.assertIsNone(report.calculation_token)

    def test_update_coverage_dates_IE(self):
        report = create_form3x(self.committee, "2024-01-01", "2024-03-31")
        # disbursement within
        ie = create_ie(
            self.committee,
            None,
            "2024-03-31",
            None,
            "2024-03-31",
            250,
            "P2026",
            None,
            report=report,
            memo_code=False,
        )

        def change_dates(report, from_date, through_date, expect_error=False):

            validated_data = {
                "coverage_from_date": from_date,
                "coverage_through_date": through_date,
            }
            serializer = Form3XSerializer(
                data=validated_data,
                context={
                    "request": self.mock_request,
                    "fields_to_ignore": [
                        "treasurer_first_name",
                        "treasurer_last_name",
                        "date_signed",
                        "form_type",
                        "filer_committee_id_number",
                    ],
                },
            )
            if expect_error:
                with self.assertRaises(Exception):
                    serializer.is_valid(raise_exception=True)
                    serializer.update(
                        report,
                        {
                            "coverage_from_date": from_date,
                            "coverage_through_date": through_date,
                        },
                    )
                return
            serializer.is_valid(raise_exception=True)
            serializer.update(
                report,
                {
                    "coverage_from_date": from_date,
                    "coverage_through_date": through_date,
                },
            )

        change_dates(report, "2024-01-01", "2024-03-31")
        change_dates(report, "2024-01-01", "2024-03-01", expect_error=True)
        change_dates(report, "2024-04-01", "2024-04-31", expect_error=True)

        # add dissem date.  ok for it to be outside range if disbursement date is inside
        ie.schedule_e.dissemination_date = datetime.strptime(
            "2023-12-31", "%Y-%m-%d"
        ).date()
        ie.schedule_e.save()
        change_dates(report, "2024-01-01", "2024-03-31")

        # should fail if disbursement date is not set and dissemination date is outside
        ie.schedule_e.disbursement_date = None
        ie.schedule_e.save()
        change_dates(report, "2024-01-01", "2024-03-31", expect_error=True)

        # ok if disbursemetn date is not set and dissem is inside
        ie.schedule_e.dissemination_date = datetime.strptime(
            "2024-02-01", "%Y-%m-%d"
        ).date()
        ie.schedule_e.save()
        change_dates(report, "2024-01-01", "2024-03-31")
