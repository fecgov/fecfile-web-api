import json

from django.http import QueryDict
from django.test import tag
from fecfiler.reports.views import ReportViewSet
from fecfiler.reports.utils.report import delete_all_reports
from fecfiler.reports.models import Report
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.views import TransactionViewSet
from fecfiler.reports.managers import STATUS_CODE_SUCCESS
from fecfiler.transactions.tests.utils import create_schedule_a, create_loan
from fecfiler.contacts.tests.utils import create_test_organization_contact
from fecfiler.transactions.schedule_c.utils import carry_forward_loan
from fecfiler.user.models import User
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.shared.viewset_test import FecfilerViewSetTest
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
        uri = "/api/v1/reports/e2e-delete-all-reports/"
        response = self.send_nonviewset_post_request(uri, {}, committee=e2e_committee)
        self.assertEqual(response.status_code, 405)
        report_count = Report.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        transaction_count = Report.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        self.assertGreater(report_count, 0)
        self.assertGreater(transaction_count, 0)

    @tag("e2e")
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
        response = self.send_viewset_post_request(
            "/api/v1/reports/e2e-delete-all-reports/",
            {},
            ReportViewSet,
            "e2e_delete_all_reports",
            committee=e2e_committee,
        )
        self.assertEqual(response.status_code, 200)

        report_count = Report.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        transaction_count = Transaction.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        self.assertEqual(report_count, 0)
        self.assertEqual(transaction_count, 0)

    @tag("e2e")
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

    @tag("e2e")
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
        self.assertEqual(retrieve_response.data["can_unamend"], False)

        response = self.send_viewset_post_request(
            f"/api/v1/reports/{report.id}/amend",
            {},
            ReportViewSet,
            "amend",
            committee=committee,
            pk=report.id,
        )
        self.assertEqual(response.status_code, 200)

        retrieve_response = self.send_viewset_get_request(
            f"/api/v1/reports/{report.id}",
            ReportViewSet,
            "retrieve",
            committee=committee,
            pk=report.id,
        )
        self.assertEqual(retrieve_response.status_code, 200)
        self.assertEqual(retrieve_response.data["report_status"], "In progress")
        self.assertEqual(retrieve_response.data["can_unamend"], True)

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
        report_retrieve_response = self.send_viewset_get_request(
            f"/api/v1/reports/{report.id}",
            ReportViewSet,
            "retrieve",
            committee=self.committee,
            pk=report.id,
        )
        self.assertEqual(report_retrieve_response.status_code, 200)
        self.assertEqual(report_retrieve_response.data["can_unamend"], False)

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

        report_retrieve_response = self.send_viewset_get_request(
            f"/api/v1/reports/{report.id}",
            ReportViewSet,
            "retrieve",
            committee=self.committee,
            pk=report.id,
        )
        self.assertEqual(report_retrieve_response.status_code, 200)
        self.assertEqual(report_retrieve_response.data["can_unamend"], True)
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

        # test that a successfully submitted report
        # with no transactions can not be unamended
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
        report_retrieve_response = self.send_viewset_get_request(
            f"/api/v1/reports/{report.id}",
            ReportViewSet,
            "retrieve",
            committee=self.committee,
            pk=report.id,
        )
        self.assertEqual(report_retrieve_response.status_code, 200)
        self.assertEqual(report_retrieve_response.data["can_unamend"], False)

        # now amend the report and add a transaction,
        # which should make the report unable to be unamended
        report.amend()

        create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            None,
            "2024-02-01",
            "100.00",
            report=report,
        )
        report_retrieve_response = self.send_viewset_get_request(
            f"/api/v1/reports/{report.id}",
            ReportViewSet,
            "retrieve",
            committee=self.committee,
            pk=report.id,
        )
        self.assertEqual(report_retrieve_response.status_code, 200)
        self.assertEqual(report_retrieve_response.data["can_unamend"], False)
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

    def test_update_version_number_success(self):
        report = create_form3x(self.committee, "2026-01-01", "2026-02-01", {})
        payload = {"amendment": "2", "eFilingId": "FEC-112233"}
        response = self.send_viewset_post_request(
            f"/api/v1/reports/{report.id}/update-version-number",
            payload,
            ReportViewSet,
            "update_version_number",
            committee=self.committee,
            pk=report.id,
        )

        self.assertEqual(response.status_code, 200)

        updated_report = Report.objects.get(id=report.id)
        self.assertEqual(updated_report.report_version, "2")
        self.assertEqual(updated_report.form_type, "F3XA")
        self.assertEqual(updated_report.fec_report_id, "FEC-112233")
        self.assertEqual(response.data["id"], str(report.id))

    def test_update_version_number_to_original(self):
        report = create_form3x(self.committee, "2026-01-01", "2026-02-01", {})
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

        payload = {"amendment": "0", "eFilingId": ""}
        response = self.send_viewset_post_request(
            f"/api/v1/reports/{report.id}/update-version-number",
            payload,
            ReportViewSet,
            "update_version_number",
            committee=self.committee,
            pk=report.id,
        )

        self.assertEqual(response.status_code, 200)

        updated_report = Report.objects.get(id=report.id)
        self.assertEqual(updated_report.report_version, None)
        self.assertEqual(updated_report.form_type, "F3XN")
        self.assertEqual(updated_report.fec_report_id, "")
        self.assertEqual(response.data["id"], str(report.id))

    def test_update_version_number_not_found(self):
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        payload = {"amendment": "1", "eFilingId": "FEC-999999"}
        response = self.send_viewset_post_request(
            f"/api/v1/reports/{fake_uuid}/update-version-number",
            payload,
            ReportViewSet,
            "update_version_number",
            committee=self.committee,
            pk=fake_uuid,
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["detail"], "Report not found.")

    def test_update_version_number_server_error(self):
        from unittest.mock import patch

        report = create_form3x(self.committee, "2026-01-01", "2026-02-01", {})
        payload = {"amendment": 3, "eFilingId": "FEC-ERROR"}

        with patch.object(
            Report, "save", side_effect=Exception("Database connection failure")
        ):
            response = self.send_viewset_post_request(
                f"/api/v1/reports/{report.id}/update-version-number",
                payload,
                ReportViewSet,
                "update_version_number",
                committee=self.committee,
                pk=report.id,
            )

            self.assertEqual(response.status_code, 500)
            self.assertIn(
                "An error occurred while updating the report", response.data["detail"]
            )

    def test_can_delete_reports_with_loan(self):
        report_1 = create_form3x(self.committee, "2026-01-01", "2026-01-31", {})
        report_2 = create_form3x(self.committee, "2026-02-01", "2026-02-28", {})
        report_3 = create_form3x(self.committee, "2026-03-01", "2026-03-31", {})

        self.assertTrue(report_1.check_can_delete())
        self.assertTrue(report_2.check_can_delete())
        self.assertTrue(report_3.check_can_delete())

        test_org = create_test_organization_contact("Test Org", self.committee.id, {})
        test_loan = create_loan(self.committee, test_org, 40000, "2120-01-31", "More")
        test_loan.add_to_report(report_1.id)

        carry_forward_loan(test_loan, report_2)
        carry_forward_loan(test_loan, report_3)

        self.assertFalse(report_1.check_can_delete())
        self.assertFalse(report_2.check_can_delete())
        self.assertTrue(report_3.check_can_delete())

        self.send_viewset_delete_request(
            f"api/v1/transactions/{test_loan.id}/",
            TransactionViewSet,
            "destroy",
            pk=test_loan.id,
        )

        self.assertTrue(report_1.check_can_delete())
        self.assertTrue(report_2.check_can_delete())
        self.assertTrue(report_3.check_can_delete())

    def test_delete_reports_with_loan_in_order(self):
        report_1 = create_form3x(self.committee, "2026-01-01", "2026-01-31", {})
        report_2 = create_form3x(self.committee, "2026-02-01", "2026-02-28", {})
        report_3 = create_form3x(self.committee, "2026-03-01", "2026-03-31", {})

        self.assertTrue(report_1.check_can_delete())
        self.assertTrue(report_2.check_can_delete())
        self.assertTrue(report_3.check_can_delete())

        test_org = create_test_organization_contact("Test Org", self.committee.id, {})
        test_loan = create_loan(self.committee, test_org, 40000, "2120-01-31", "More")
        test_loan.add_to_report(report_1.id)

        carry_forward_loan(test_loan, report_2)
        carry_forward_loan(test_loan, report_3)

        self.assertFalse(report_1.check_can_delete())
        self.assertFalse(report_2.check_can_delete())
        self.assertTrue(report_3.check_can_delete())

        delete_1_response = self.send_viewset_delete_request(
            f"api/v1/transactions/{report_1.id}/",
            ReportViewSet,
            "destroy",
            pk=report_1.id,
        )

        self.assertEqual(delete_1_response.status_code, 400)

        delete_2_response = self.send_viewset_delete_request(
            f"api/v1/transactions/{report_2.id}/",
            ReportViewSet,
            "destroy",
            pk=report_2.id,
        )

        self.assertEqual(delete_2_response.status_code, 400)

        self.send_viewset_delete_request(
            f"api/v1/transactions/{report_3.id}/",
            ReportViewSet,
            "destroy",
            pk=report_3.id,
        )

        self.send_viewset_delete_request(
            f"api/v1/transactions/{report_2.id}/",
            ReportViewSet,
            "destroy",
            pk=report_2.id,
        )

        self.send_viewset_delete_request(
            f"api/v1/transactions/{report_1.id}/",
            ReportViewSet,
            "destroy",
            pk=report_1.id,
        )

        test_reports = Report.objects.filter(
            id__in=[report_1.id, report_2.id, report_3.id]
        )

        self.assertFalse(test_reports.exists())
