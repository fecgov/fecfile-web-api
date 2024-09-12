from decimal import Decimal
from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework import status
from fecfiler.user.models import User
from fecfiler.reports.models import Report
import json
from copy import deepcopy
from fecfiler.transactions.views import TransactionViewSet, TransactionOrderingFilter
from fecfiler.transactions.models import Transaction
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.views import create_committee_view
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.contacts.tests.utils import (
    create_test_individual_contact,
    create_test_candidate_contact,
)
from fecfiler.transactions.tests.utils import (
    create_schedule_a,
    create_schedule_b,
    create_loan,
    create_ie,
)
import structlog

logger = structlog.get_logger(__name__)


class TransactionViewsTestCase(TestCase):

    json_content_type = "application/json"

    @classmethod
    def setUpClass(cls):
        return super().setUpClass()

    def setUp(self):
        self.factory = RequestFactory()
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.user = User.objects.create(email="test@fec.gov", username="gov")
        create_committee_view(self.committee.id)
        self.q1_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        self.contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id
        )
        self.contact_2 = create_test_candidate_contact(
            "last name", "First name", self.committee.id, "H8MA03131", "S", "AK", "01"
        )
        self.transaction = create_ie(
            self.committee,
            self.contact_1,
            "2023-01-12",
            "2023-01-15",
            "153.00",
            "C2012",
            self.contact_2,
        )
        self.payloads = json.load(
            open("fecfiler/transactions/fixtures/view_payloads.json")
        )
        create_schedule_b(
            "GENERAL_DISBURSEMENT",
            self.committee,
            self.contact_1,
            "2023-09-02",
            "3.00",
            "GENERAL_DISBURSEMENT",
        )

        self.ordering_filter = TransactionOrderingFilter()
        self.view = TransactionViewSet()

        request = self.factory.get(
            "/api/v1/transactions/",
            content_type=self.json_content_type,
        )
        request.query_params = {
            "ordering": "memo_code",
            "report_id": self.q1_report.id,
        }
        request.session = {
            "committee_uuid": self.committee.id,
            "committee_id": self.committee.committee_id,
        }
        self.view.request = request

    def create_trans_from_data(self, receipt_data):
        create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_1,
            receipt_data["date"],
            receipt_data["amount"],
            group=receipt_data["group"],
            report=self.q1_report,
            memo_code=receipt_data["memo"],
        )

    def request(self, payload, params={}):
        request = self.factory.post(
            "/api/v1/transactions",
            json.dumps(payload),
            content_type=self.json_content_type,
        )
        request.user = self.user
        request.data = deepcopy(payload)
        request.query_params = params
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        return request

    def test_save_transaction_pair(self):
        request = self.request(self.payloads["IN_KIND"])
        transaction = TransactionViewSet().save_transaction(request.data, request)
        self.assertEqual("John", transaction.contact_1.first_name)
        self.assertEqual("Smith", transaction.contact_1.last_name)

    def test_update(self):
        request = self.request(self.payloads["IN_KIND"])
        transaction = TransactionViewSet().save_transaction(request.data, request)
        updated_payload = deepcopy(self.payloads["IN_KIND"])
        updated_payload["id"] = str(transaction.id)
        updated_payload["contribution_amount"] = 999
        updated_payload["children"][0]["id"] = str(transaction.children[0].id)
        updated_payload["children"][0]["expenditure_amount"] = 999
        request = self.request(updated_payload)
        transaction = TransactionViewSet().save_transaction(request.data, request)
        updated_transaction = Transaction.objects.get(id=transaction.id)
        self.assertEqual(updated_transaction.schedule_a.contribution_amount, 999)
        self.assertEqual(
            updated_transaction.children[0].schedule_b.expenditure_amount, 999
        )

    def test_get_queryset(self):
        for i in range(8):
            create_schedule_a(
                "INDIVIDUAL_RECEIPT",
                self.committee,
                self.contact_1,
                "2023-01-01",
                str((i + 1) * 10),
                "GENERAL",
            )

        for i in range(2):
            create_loan(
                self.committee, self.contact_1, Decimal((i + 1) * 10), "2023-09-20", "2.0"
            )

        view_set = TransactionViewSet()
        view_set.request = self.request({}, {"schedules": "A,B,C,C2,D,E"})
        self.assertEqual(view_set.get_queryset().count(), 12)
        view_set.request = self.request({}, {"schedules": "A,B,D,E"})
        self.assertEqual(view_set.get_queryset().count(), 10)
        view_set.request = self.request({}, {"schedules": ""})
        self.assertEqual(view_set.get_queryset().count(), 0)

    def test_get_previous_entity(self):
        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        view_set.request = self.request({}, {"contact_1_id": str(self.contact_1.id)})
        # leave out required params
        response = view_set.previous_transaction_by_entity(view_set.request)
        self.assertEqual(response.status_code, 400)

        response = view_set.previous_transaction_by_entity(
            self.request(
                {},
                {
                    "contact_1_id": str(self.contact_1.id),
                    "date": "2023-09-20",
                    "aggregation_group": "GENERAL_DISBURSEMENT",
                },
            )
        )
        self.assertEqual(response.data["date"], "2023-09-02")

        response = view_set.previous_transaction_by_entity(
            self.request(
                {},
                {
                    "contact_1_id": str(self.contact_1.id),
                    "date": "2024-09-20",
                    "aggregation_group": "GENERAL_DISBURSEMENT",
                },
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_get_previous_election(self):
        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        view_set.request = self.request(
            {},
            {
                "date": "2023-09-20",
                "aggregation_group": "INDEPENDENT_EXPENDITURE",
                "election_code": "C2012",
                "candidate_office": "S",
            },
        )
        # leave out required params
        response = view_set.previous_transaction_by_election(view_set.request)
        self.assertEqual(response.status_code, 400)
        view_set.request = self.request(
            {},
            {
                "date": "2023-09-20",
                "aggregation_group": "INDEPENDENT_EXPENDITURE",
                "election_code": "C2012",
                "candidate_office": "H",
                "candidate_state": "AK",
            },
        )
        # leave out required params
        response = view_set.previous_transaction_by_election(view_set.request)
        self.assertEqual(response.status_code, 400)

        view_set.request = self.request(
            {},
            {
                "date": "2023-10-31",
                "aggregation_group": "INDEPENDENT_EXPENDITURE",
                "election_code": "C2012",
                "candidate_office": "S",
                "candidate_state": "AK",
                "candidate_district": "01",
            },
        )
        response = view_set.previous_transaction_by_election(view_set.request)
        transaction = response.data

        self.assertEqual(transaction.get("date"), "2023-01-12")

    def test_inherited_election_aggregate(self):
        request = self.factory.get(f"/api/v1/transactions/{self.transaction.id}/")
        request.user = self.user
        request.query_params = {}
        request.data = {}
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }

        view = TransactionViewSet
        view.request = request

        response = view.as_view({"get": "retrieve"})(request, pk=str(self.transaction.id))
        transaction = response.data
        logger.debug(transaction)
        self.assertEqual(transaction.get("_calendar_ytd_per_election_office"), "153.00")

    def test_reatt_redes_multisave_transactions(self):
        txn1 = deepcopy(self.payloads["IN_KIND"])
        txn1["contributor_last_name"] = "one"
        txn2 = deepcopy(self.payloads["IN_KIND"])
        txn2["contributor_last_name"] = "two"
        txn3 = deepcopy(self.payloads["IN_KIND"])
        txn3["contributor_last_name"] = "three"
        txn2["children"] = [txn3]
        payload = [txn1, txn2]

        view_set = TransactionViewSet()
        response = view_set.save_reatt_redes_transactions(self.request(payload))
        transactions = response.data
        self.assertEqual(len(transactions), 2)

    def test_add_transaction_to_report(self):
        report_id = str(self.q1_report.id)
        transaction_id = str(self.transaction.id)

        payload = {"transaction_id": transaction_id, "report_id": report_id}
        view_set = TransactionViewSet()
        response = view_set.add_transaction_to_report(self.request(payload))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, "Transaction added to report")

        # Verify that the report is added to the transaction
        transaction = Transaction.objects.get(id=transaction_id)
        self.assertEqual(transaction.reports.count(), 1)
        self.assertEqual(str(transaction.reports.first().id), report_id)

        # Verify that the report has the transaction
        report = Report.objects.get(id=report_id)
        transaction_ids = [str(t.id) for t in report.transactions.all()]
        self.assertIn(transaction_id, transaction_ids)

        # Verify response when no transaction id provided
        payload["transaction_id"] = None
        response = view_set.add_transaction_to_report(self.request(payload))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, "No transaction matching id provided")

        # Verify response when non existing report id provided
        payload["transaction_id"] = str(self.transaction.id)
        payload["report_id"] = "474a1a10-da68-4d71-9a11-cccccccccccc"
        response = view_set.add_transaction_to_report(self.request(payload))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, "No report matching id provided")

    def test_remove_transaction_from_report(self):
        report_id = str(self.q1_report.id)
        transaction_id = str(self.transaction.id)

        payload = {"transaction_id": transaction_id, "report_id": report_id}
        view_set = TransactionViewSet()
        response = view_set.remove_transaction_from_report(self.request(payload))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, "Transaction removed from report")

        # Verify that the report is added to the transaction
        transaction = Transaction.objects.get(id=transaction_id)
        self.assertEqual(transaction.reports.count(), 0)

        # Verify that the report does not have the transaction
        report = Report.objects.get(id=report_id)
        transaction_ids = [str(t.id) for t in report.transactions.all()]
        self.assertNotIn(str(transaction_id), transaction_ids)

        # Verify response when no transaction id provided
        payload["transaction_id"] = None
        response = view_set.remove_transaction_from_report(self.request(payload))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, "No transaction matching id provided")

        # Verify response when non existing report id provided
        payload["transaction_id"] = str(self.transaction.id)
        payload["report_id"] = "474a1a10-da68-4d71-9a11-cccccccccccc"
        response = view_set.remove_transaction_from_report(self.request(payload))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, "No report matching id provided")

    def test_save_debt(self):
        payload = self.payloads["DEBT"]
        payload["report_ids"] = [str(self.q1_report.id)]
        view_set = TransactionViewSet()
        response = view_set.create(self.request(payload))
        report_coverage_from_date = self.q1_report.coverage_from_date
        debt_id = response.data
        self.assertEqual(response.status_code, 200)
        debt = Transaction.objects.get(id=debt_id)
        self.assertEqual(
            debt.schedule_d.report_coverage_from_date.strftime("%Y-%m-%d"),
            report_coverage_from_date,
        )

    def test_sorting_memo_code(self):
        indiviual_receipt_data = [
            {"date": "2023-01-01", "amount": "123.45", "group": "GENERAL", "memo": False},
            {"date": "2024-01-01", "amount": "100.00", "group": "GENERAL", "memo": None},
            {"date": "2024-01-02", "amount": "200.00", "group": "GENERAL", "memo": True},
            {"date": "2024-01-03", "amount": "100.00", "group": "OTHER", "memo": True},
        ]
        for receipt_data in indiviual_receipt_data:
            self.create_trans_from_data(receipt_data)

        transactions = Transaction.objects.filter(committee_account_id=self.committee.id)
        memos_sorted = transactions.order_by("memo_code")

        ordered_queryset = self.ordering_filter.filter_queryset(
            self.view.request, transactions, self.view
        )
        self.assertEqual(ordered_queryset.first().id, memos_sorted.first().id)

    def test_sorting_memo_code_inverted(self):
        indiviual_receipt_data = [
            {"date": "2023-01-01", "amount": "123.45", "group": "GENERAL", "memo": False},
            {"date": "2024-01-01", "amount": "100.00", "group": "GENERAL", "memo": None},
            {"date": "2024-01-02", "amount": "200.00", "group": "GENERAL", "memo": True},
            {"date": "2024-01-03", "amount": "100.00", "group": "OTHER", "memo": True},
        ]
        for receipt_data in indiviual_receipt_data:
            self.create_trans_from_data(receipt_data)
        self.view.request.query_params["ordering"] = "-memo_code"

        transactions = self.view.get_queryset().filter(
            committee_account_id=self.committee.id
        )
        memos_inverted = transactions.order_by("-memo_code")

        ordered_queryset = self.ordering_filter.filter_queryset(
            self.view.request, transactions, self.view
        )
        self.assertEqual(ordered_queryset.first().id, memos_inverted.first().id)

    def test_sorting_memos_only_true(self):
        indiviual_receipt_data = [
            {"date": "2023-01-01", "amount": "123.45", "group": "GENERAL", "memo": True},
            {"date": "2024-01-01", "amount": "100.00", "group": "GENERAL", "memo": True},
            {"date": "2024-01-02", "amount": "200.00", "group": "GENERAL", "memo": True},
            {"date": "2024-01-03", "amount": "100.00", "group": "OTHER", "memo": True},
        ]
        for receipt_data in indiviual_receipt_data:
            self.create_trans_from_data(receipt_data)
        self.view.request.query_params["ordering"] = "-memo_code"

        transactions = self.view.get_queryset().filter(
            committee_account_id=self.committee.id
        )
        memos_sorted = transactions.order_by("memo_code")

        parsed_ordering = self.ordering_filter.get_ordering(
            self.view.request, transactions, self.view
        )
        self.assertListEqual(parsed_ordering, ["memo_code"])

        ordered_queryset = self.ordering_filter.filter_queryset(
            self.view.request, transactions, self.view
        )
        self.assertEqual(ordered_queryset.first().id, memos_sorted.first().id)

    def test_multi_sorting(self):
        indiviual_receipt_data = [
            {"date": "2023-01-01", "amount": "200.00", "group": "GENERAL", "memo": True},
            {"date": "2024-01-01", "amount": "300.00", "group": "GENERAL", "memo": True},
            {"date": "2024-01-02", "amount": "100.00", "group": "GENERAL", "memo": False},
            {"date": "2024-01-03", "amount": "400.00", "group": "OTHER", "memo": False},
        ]
        for receipt_data in indiviual_receipt_data:
            self.create_trans_from_data(receipt_data)

        transactions = self.view.get_queryset().filter(
            committee_account_id=self.committee.id
        )
        self.view.request.query_params["ordering"] = "memo_code, amount"
        memos_sorted = transactions.order_by("memo_code", "amount")

        ordered_queryset = self.ordering_filter.filter_queryset(
            self.view.request, transactions, self.view
        )
        self.assertEqual(ordered_queryset.count(), len(indiviual_receipt_data))
        for i in range(ordered_queryset.count()):
            self.assertEqual(ordered_queryset[i].id, memos_sorted[i].id)

    def test_destroy(self):
        view_set = TransactionViewSet()
        request = self.factory.delete(f"/api/v1/transactions/{self.transaction.pk}/")
        response = view_set.destroy(request, pk=self.transaction.pk)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Transaction.objects.filter(pk=self.transaction.pk).exists())
