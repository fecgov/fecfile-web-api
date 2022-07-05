from django.test import TestCase
from .models import SchATransaction


class SchATransactionsViewTest(TestCase):
    fixtures = ["test_committee_accounts", "test_f3x_summaries", "test_scha_transactions"]

    def setUp(self):
        self.f3x = 1
        self.f3x_2 = 2
        self.f3x_transaction_count = len(SchATransaction.objects.filter(
            report_id = self.f3x))
        self.f3x_2_transaction_count= len(SchATransaction.objects.filter(
            report_id = self.f3x_2))

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get(f'/api/v1/sch-a-transactions/?report_id={self.f3x}')
        self.assertEqual(response.status_code, 200)

    def test_url_requires_no_report_id(self):
        response = self.client.get(f'/api/v1/sch-a-transactions/')
        parsed_response = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            parsed_response["count"],
            self.f3x_transaction_count+self.f3x_2_transaction_count
        )

    def test_is_paginated(self):
        response = self.client.get(f'/api/v1/sch-a-transactions/?report_id={self.f3x}')
        parsed_response = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(parsed_response["count"], self.f3x_transaction_count)
        self.assertEqual(len(parsed_response["results"]), 10)

    def test_only_from_one_report(self):
        response_f3x = self.client.get(
            f'/api/v1/sch-a-transactions/?report_id={self.f3x}')
        response_f3x_2=self.client.get(
            f'/api/v1/sch-a-transactions/?report_id={self.f3x_2}')
        self.assertNotEqual(response_f3x.json()["count"], response_f3x_2.json()["count"])
