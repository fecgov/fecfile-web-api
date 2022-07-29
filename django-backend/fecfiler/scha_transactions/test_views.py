from django.test import TestCase, RequestFactory
from .models import SchATransaction
from .views import SchATransactionViewSet
from ..authentication.models import Account


class SchATransactionsViewTest(TestCase):
    fixtures = [
        "test_committee_accounts",
        "test_f3x_summaries",
        "test_scha_transactions",
        "test_accounts",
    ]

    def setUp(self):
        self.f3x = 1
        self.f3x_2 = 2
        self.f3x_transaction_count = len(
            SchATransaction.objects.filter(report_id=self.f3x)
        )
        self.f3x_2_transaction_count = len(
            SchATransaction.objects.filter(report_id=self.f3x_2)
        )

        self.user = Account.objects.get(cmtee_id="C12345678")
        self.factory = RequestFactory()

    def test_view_url_exists_at_desired_location(self):
        request = self.factory.get(f"/api/v1/sch-a-transactions/?report_id={self.f3x}")
        request.user = self.user
        response = SchATransactionViewSet.as_view({"get": "list"})(request)
        self.assertEqual(response.status_code, 200)

    def test_is_paginated(self):
        request = self.factory.get(f"/api/v1/sch-a-transactions/?report_id={self.f3x}")
        request.user = self.user
        response = SchATransactionViewSet.as_view({"get": "list"})(request)

        response.render()
        parsed_response = response.data

        self.assertEqual(response.status_code, 200)
        self.assertEqual(parsed_response["count"], self.f3x_transaction_count)
        self.assertEqual(len(parsed_response["results"]), 10)

    def test_only_from_one_report(self):
        responses = []
        for url in [
            f"/api/v1/sch-a-transactions/?report_id={self.f3x}",
            f"/api/v1/sch-a-transactions/?report_id={self.f3x_2}",
        ]:
            request = self.factory.get(url)
            request.user = self.user
            response = SchATransactionViewSet.as_view({"get": "list"})(request)

            response.render()
            responses.append(response.data)

        self.assertNotEqual(responses[0]["count"], responses[1]["count"])
