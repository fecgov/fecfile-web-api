from django.test import TestCase, RequestFactory
from .views import F3XSummaryViewSet
from ..authentication.models import Account


class F3XSummaryViewSetTest(TestCase):
    fixtures = ["test_f3x_summaries", "test_committee_accounts", "test_accounts"]

    def setUp(self):
        self.user = Account.objects.get(cmtee_id="C12345678")
        self.factory = RequestFactory()

    def test_coverage_dates_happy_path(self):
        self.assertEqual(True, True)
        request = self.factory.get("/api/v1/f3x-summaries/coverage_dates")
        request.user = self.user

        response = F3XSummaryViewSet.as_view({"get": "coverage_dates"})(request)

        expected_json = [
            {
                "coverage_from_date": "2005-01-30",
                "coverage_through_date": "2005-02-28",
                "report_code": "Q1",
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
