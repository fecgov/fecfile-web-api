from django.test import TestCase, RequestFactory
from .views import F3XSummaryViewSet
from ..authentication.models import Account


class F3XSummaryViewSetTest(TestCase):
    fixtures = ["test_db_f3x_summaries", "test_committee_accounts", "test_accounts"]

    def setUp(self):
        self.user = Account.objects.get(cmtee_id="C00123456")
        self.factory = RequestFactory()

    def test_coverage_dates_happy_path(self):
        self.assertEqual(True, True)
        request = self.factory.get('/api/v1/f3x-summaries/coverage_dates')
        request.user = self.user
        request.user.cmtee_id = "C00277608"

        response = F3XSummaryViewSet.as_view({"get": "coverage_dates"})(request)

        expectedJson = [
          {
            "report_code": "MY",
            "coverage_from_date": "2021-01-20",
            "coverage_through_date": "2022-05-25"
          },
          {
            "report_code": "M9",
            "coverage_from_date": "2021-01-21",
            "coverage_through_date": "2021-09-07"
          },
          {
            "report_code": "MY",
            "coverage_from_date": "2021-01-21",
            "coverage_through_date": "2022-01-03"
          },
          {
            "report_code": "M5",
            "coverage_from_date": "2021-01-21",
            "coverage_through_date": "2022-02-05"
          },
          {
            "report_code": "M12",
            "coverage_from_date": "2021-01-21",
            "coverage_through_date": "2022-11-15"
          }
        ]

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            expectedJson
        )
