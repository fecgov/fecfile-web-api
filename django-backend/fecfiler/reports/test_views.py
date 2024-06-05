from django.test import RequestFactory, TestCase
from fecfiler.reports.views import ReportViewSet
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
        for i in range(10):
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
