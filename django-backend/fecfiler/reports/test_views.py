from uuid import UUID
from django.http import QueryDict
from django.test import RequestFactory, TestCase
from fecfiler.reports.views import ReportViewSet, delete_all_reports
from fecfiler.reports.models import Report
from fecfiler.transactions.models import Transaction
from fecfiler.user.models import User
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.views import create_committee_view
from fecfiler.reports.tests.utils import create_form3x
import structlog

logger = structlog.get_logger(__name__)


class CommitteeMemberViewSetTest(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.user = User.objects.create(email="test@fec.gov", username="gov")
        create_committee_view(self.committee.id)
        self.factory = RequestFactory()

    def test_list_paginated(self):
        for _ in range(10):
            create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        view = ReportViewSet()
        view.format_kwarg = "format"
        request = self.factory.get("/api/v1/reports")
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        request.method = "GET"
        request.query_params = {"page": 1}
        view.request = request
        response = view.list(request)
        self.assertEqual(len(response.data["results"]), 10)

    def test_list_no_pagination(self):
        view = ReportViewSet()
        view.format_kwarg = "format"
        request = self.factory.get("/api/v1/reports")
        request.user = self.user
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        request.method = "GET"
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
        request = self.factory.get("/api/v1/reports")
        request.user = self.user
        request.session = {
            "committee_uuid": UUID("11111111-2222-3333-4444-555555555555"),
            "committee_id": "C01234567",
        }
        request.method = "GET"
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

    def test_e2e_delete_all_reports(self):
        view = ReportViewSet()

        e2e_committee = CommitteeAccount(committee_id="C99999999")
        e2e_committee.save()

        new_report = Report(
            committee_account=e2e_committee
        )
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

        view.format_kwarg = "format"
        request = self.factory.post("/api/v1/reports/e2e-delete-all-reports")
        request.user = self.user
        request.session = {
            "committee_uuid": UUID("11111111-2222-3333-4444-555555555555"),
            "committee_id": "C01234567",
        }
        request.query_params = QueryDict({})
        request.method = "POST"
        view.request = request
        view.e2e_delete_all_reports(request)

        report_count = Report.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        transaction_count = Report.objects.filter(
            committee_account__committee_id="C99999999"
        ).count()
        self.assertEqual(report_count, 0)
        self.assertEqual(transaction_count, 0)

    def test_delete_all_reports_for_a_committee(self):
        committee = CommitteeAccount.objects.get(committee_id="C00000000")

        new_report = Report(
            committee_account=committee
        )
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
