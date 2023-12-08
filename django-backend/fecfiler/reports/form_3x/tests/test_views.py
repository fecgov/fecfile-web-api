from django.test import TestCase, RequestFactory

from fecfiler.reports.models import Report
from ..views import Form3XViewSet
from fecfiler.authentication.models import Account

from rest_framework.test import force_authenticate


class Form3XViewSetTest(TestCase):
    fixtures = ["test_f3x_reports", "test_committee_accounts", "test_accounts"]

    def setUp(self):
        self.user = Account.objects.get(cmtee_id="C12345678")
        self.factory = RequestFactory()

    def test_coverage_dates_happy_path(self):
        self.assertEqual(True, True)
        request = self.factory.get("/api/v1/reports/form-f3x/coverage_dates")
        request.user = self.user

        response = Form3XViewSet.as_view({"get": "coverage_dates"})(request)

        expected_json = [
            {
                "coverage_from_date": "2005-01-30",
                "coverage_through_date": "2005-02-28",
                "report_code": "Q1",
            },
            {
                "coverage_from_date": "2005-03-01",
                "coverage_through_date": "2005-03-31",
                "report_code": "M4",
            },
            {
                "coverage_from_date": "2006-01-30",
                "coverage_through_date": "2006-02-28",
                "report_code": "MY",
            },
            {
                "coverage_from_date": "2007-01-30",
                "coverage_through_date": "2007-02-28",
                "report_code": "12C",
            },
        ]

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding="utf8"), expected_json)

    def test_amend(self):
        request = self.factory.post(
            "/api/v1/reports/1406535e-f99f-42c4-97a8-247904b7d297/amend/"
        )
        request.user = self.user
        force_authenticate(request, self.user)
        view = Form3XViewSet.as_view({"post": "amend"})
        response = view(request, pk="1406535e-f99f-42c4-97a8-247904b7d297")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Report.objects.filter(id="1406535e-f99f-42c4-97a8-247904b7d297")
            .first()
            .form_type,
            "F3XA",
        )
