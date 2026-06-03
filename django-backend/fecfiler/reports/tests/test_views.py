import json

from django.http import QueryDict
from fecfiler.reports.views import ReportViewSet
from fecfiler.reports.utils.report import delete_all_reports
from fecfiler.reports.models import Report
from fecfiler.transactions.models import Transaction
from fecfiler.reports.managers import STATUS_CODE_SUCCESS
from fecfiler.transactions.tests.utils import create_schedule_a
from fecfiler.user.models import User
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.shared.viewset_test import FecfilerViewSetTest
from unittest.mock import patch
from fecfiler.web_services.models import FECStatus, UploadSubmission
import structlog

logger = structlog.get_logger(__name__)


class ReportViewSetTest(FecfilerViewSetTest):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        user = User.objects.create(email="test@fec.gov", username="gov")
        super().set_default_user(user)
        super().set_default_committee(self.committee)
        super().setUp()

    def test_list_paginated(self):
        for _ in range(10):
            create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        view = ReportViewSet()
        view.format_kwarg = "format"
        request = self.build_viewset_get_request("/api/v1/reports")
        request.query_params = {"page": 1}
        view.request = request
        response = view.list(request)
        self.assertEqual(len(response.data["results"]), 10)

    def test_list_no_pagination(self):
        view = ReportViewSet()
        view.format_kwarg = "format"
        request = self.build_viewset_get_request("/api/v1/reports")
        request.query_params = {}
        view.request = request
        response = view.list(request)
        try:
            response.data["results"]  # A non-paginated response will throw an error here
            self.assertTrue(response is None)
        except TypeError:
            self.assertTrue(response is not None)

    def test_ordering(self):
        view = ReportViewSet()
        view.format_kwarg = "format"
        request = self.build_viewset_get_request("/api/v1/reports")
        q = QueryDict(mutable=True)
        q["ordering"] = "form_type"
        q["page"] = 1
        request.query_params = q
        view.request = request
        response = view.list(request)

        self.assertEqual(response.status_code, 200)
        results = response.data["results"]
        # Check that the results are ordered correctly
        form_type_ordering = {
            "F1MN": 10,
            "F1MA": 10,
            "F3XN": 20,
            "F3XA": 20,
            "F3XT": 20,
            "F24N": 30,
            "F24A": 30,
            "F99": 40,
        }
        last_ordering = -1
        for result in results:
            form_type = result["form_type"]
            ordering = form_type_ordering.get(form_type, 0)
            self.assertGreaterEqual(ordering, last_ordering)
            last_ordering = ordering

    @patch("fecfiler.reports.views.settings.E2E_TEST", False)
    def test_e2e_delete_all_reports_not_allowed(self):
        e2e_committee = CommitteeAccount(committee_id="C99999999")
        e2e_committee.save()

        new_report = Report(committee_account=e2e_committee)
        new_report.save()

        new_transaction = Transaction(committee_account=e2e_committee)
        new_transaction.save()
        report_count = Report.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        transaction_count = Report.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        self.assertGreater(report_count, 0)
        self.assertGreater(transaction_count, 0)

        response = self.client.post(
            "/api/v1/reports/e2e-delete-all-reports/", data={}, format="json"
        )
        self.assertEqual(response.status_code, 403)
        report_count = Report.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        transaction_count = Report.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        self.assertGreater(report_count, 0)
        self.assertGreater(transaction_count, 0)

    def test_e2e_delete_all_reports(self):
        view = ReportViewSet()

        e2e_committee = CommitteeAccount(committee_id="C99999999")
        e2e_committee.save()

        new_report = Report(committee_account=e2e_committee)
        new_report.save()

        new_transaction = Transaction(committee_account=e2e_committee)
        new_transaction.save()

        report_count = Report.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        transaction_count = Transaction.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        self.assertGreater(report_count, 0)
        self.assertGreater(transaction_count, 0)

        view.format_kwarg = "format"
        request = self.build_viewset_post_request(
            "/api/v1/reports/e2e-delete-all-reports", {}
        )
        request.query_params = QueryDict({})
        view.request = request
        view.e2e_delete_all_reports(request)

        report_count = Report.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        transaction_count = Transaction.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        self.assertEqual(report_count, 0)
        self.assertEqual(transaction_count, 0)

    def test_delete_all_reports_for_a_committee(self):
        committee = CommitteeAccount.objects.get(committee_id="C00000000")

        new_report = Report(committee_account=committee)
        new_report.save()

        new_transaction = Transaction(committee_account=committee)
        new_transaction.save()

        report_count = Report.objects.filter(
            committee_account__committee_id="C00000000"
        ).count()
        transaction_count = Report.objects.filter(
            committee_account__committee_id="C00000000"
        ).count()
        self.assertGreater(report_count, 0)
        self.assertGreater(transaction_count, 0)

        delete_all_reports(committee_id="C00000000")

        report_count = Report.objects.filter(
            committee_account__committee_id="C00000000"
        ).count()
        transaction_count = Report.objects.filter(
            committee_account__committee_id="C00000000"
        ).count()
        self.assertEqual(report_count, 0)
        self.assertEqual(transaction_count, 0)

    def test_delete_all_reports_for_a_different_committee(self):
        committee = CommitteeAccount.objects.get(committee_id="C00000000")

        new_report = Report(committee_account=committee)
        new_report.save()

        new_transaction = Transaction(committee_account=committee)
        new_transaction.save()

        report_count = Report.objects.filter(
            committee_account__committee_id="C00000000"
        ).count()
        transaction_count = Report.objects.filter(
            committee_account__committee_id="C00000000"
        ).count()
        self.assertGreater(report_count, 0)
        self.assertGreater(transaction_count, 0)

        delete_all_reports(committee_id="C01234567")

        new_report_count = Report.objects.filter(
            committee_account__committee_id="C00000000"
        ).count()
        new_transaction_count = Transaction.objects.filter(
            committee_account__committee_id="C00000000"
        ).count()
        self.assertEqual(report_count, new_report_count)
        self.assertEqual(transaction_count, new_transaction_count)

    def test_amend(self):
        """Test that a successfully submitted report can be amended."""
        committee = CommitteeAccount.objects.create(committee_id="C00000001")
        report = create_form3x(committee, "2026-01-01", "2026-02-01", {})
        submission = UploadSubmission.objects.initiate_submission(
            str(report.id),
        )
        submission.save_fec_response(
            json.dumps(
                {
                    "submission_id": "fake_submission_id",
                    "status": FECStatus.ACCEPTED.value,
                    "message": "Test Save Response",
                    "report_id": "1234",
                }
            )
        )
        self.assertEqual(
            Report.objects.get(id=report.id).report_status,
            STATUS_CODE_SUCCESS,
        )

        retrieve_response = self.send_viewset_get_request(
            f"/api/v1/reports/{report.id}",
            ReportViewSet,
            "retrieve",
            committee=committee,
            pk=report.id,
        )
        self.assertEqual(retrieve_response.status_code, 200)
        self.assertEqual(retrieve_response.data["report_status"], "Submission success")
        logger.warning(f"how many reports {Report.objects.filter(id=report.id).count()}")
        request = self.build_viewset_post_request(
            f"/api/v1/reports/{report.id}/amend",
            {},
            {},
            True,
            None,
            committee=committee,
        )
        request.query_params = {}
        view = ReportViewSet()
        view.request = request
        view.action = "amend"
        view.kwargs = {"pk": report.id}
        report_from_view = view.get_object()

        logger.error(
            f"test report_from_view id {report_from_view.id} "
            f"status {report_from_view.report_status}"
        )
        report = Report.objects.get(id=report.id)
        logger.error(f"test report id {report.id} status {report.report_status}")
        self.assertEqual(report.report_status, STATUS_CODE_SUCCESS)

        response = self.send_viewset_post_request(
            f"/api/v1/reports/{report.id}/amend",
            {},
            ReportViewSet,
            "amend",
            committee=committee,
            pk=report.id,
        )
        self.assertEqual(response.status_code, 200)

    def test_unable_to_amend(self):
        """Test that an in progress report cannot be amended,
        but a successfully submitted report can be amended."""
        report = create_form3x(self.committee, "2026-01-01", "2026-02-01", {})
        response = self.send_viewset_post_request(
            f"/api/v1/reports/{report.id}/amend",
            {},
            ReportViewSet,
            "amend",
            committee=self.committee,
            pk=report.id,
        )
        # cannot be amended because report_status is not STATUS_CODE_SUCCESS
        self.assertEqual(response.status_code, 400)

    def test_unamend(self):
        """Test an amended report can be unamended."""
        report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        response = self.send_viewset_post_request(
            f"/api/v1/reports/{report.id}/unamend",
            {},
            ReportViewSet,
            "unamend",
            committee=self.committee,
            pk=report.id,
        )
        # cannot be unamended because report has not been amended
        self.assertEqual(response.status_code, 400)

        submission = UploadSubmission.objects.initiate_submission(
            str(report.id),
        )
        submission.save_fec_response(
            json.dumps(
                {
                    "submission_id": "fake_submission_id",
                    "status": FECStatus.ACCEPTED.value,
                    "message": "Test Save Response",
                    "report_id": "1234",
                }
            )
        )
        report.amend()

        response = self.send_viewset_post_request(
            f"/api/v1/reports/{report.id}/unamend",
            {},
            ReportViewSet,
            "unamend",
            committee=self.committee,
            pk=report.id,
        )

        self.assertEqual(response.status_code, 200)

        report.amend()

        create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            None,
            "2024-02-01",
            "100.00",
            report=report,
        )
        response = self.send_viewset_post_request(
            f"/api/v1/reports/{report.id}/unamend",
            {},
            ReportViewSet,
            "unamend",
            committee=self.committee,
            pk=report.id,
        )
        # cannot be unamended because we added a transaction
        self.assertEqual(response.status_code, 400)
