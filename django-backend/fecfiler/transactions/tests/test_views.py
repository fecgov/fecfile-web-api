from decimal import Decimal
from django.test import TestCase
from django.test.client import RequestFactory
from rest_framework import status
from rest_framework.request import HttpRequest, Request
from rest_framework.test import force_authenticate
from fecfiler.user.models import User
from fecfiler.reports.models import Report
import json
from copy import deepcopy
from fecfiler.transactions.views import TransactionViewSet, TransactionOrderingFilter
from fecfiler.transactions.models import Transaction
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.contacts.tests.utils import (
    create_test_committee_contact,
    create_test_individual_contact,
    create_test_candidate_contact,
    create_test_organization_contact,
)
from fecfiler.transactions.tests.utils import (
    create_schedule_a,
    create_schedule_b,
    create_loan,
    create_debt,
    create_ie,
    create_schedule_f,
    gen_schedule_f_request_data,
)
from fecfiler.transactions.serializers import TransactionSerializer
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
        self.q1_report = create_form3x(self.committee, "2024-01-01", "2024-02-01", {})
        self.q2_report = create_form3x(self.committee, "2024-02-02", "2024-03-01", {})
        self.contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id, {
                "street_1": "123 test street",
                "city": "testville",
                "state": "AK",
                "zip": "12345",
            }
        )
        self.contact_2 = create_test_candidate_contact(
            "last name", "First name", self.committee.id, "H8MA03131", "S", "AK", "01"
        )
        self.contact_3 = create_test_individual_contact(
            "last name",
            "First name",
            self.committee.id,
            {"street_1": "Test St", "city": "Testville", "state": "IL", "zip": "12345"},
        )
        self.contact_comm = create_test_committee_contact(
            "TEST COMMITTEES UNITED",
            "C12344321",
            self.committee.id,
            {"street_1": "Test St", "city": "Testville", "state": "IL", "zip": "12345"},
        )
        self.transaction = create_ie(
            self.committee,
            self.contact_1,
            "2023-01-12",
            "2023-01-15",
            "2023-01-15",
            "153.00",
            "C2012",
            self.contact_2,
        )
        self.transaction_2 = create_ie(
            self.committee,
            self.contact_1,
            "2023-01-22",
            "2023-01-25",
            "2023-01-25",
            "147.00",
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

        self.test_com_contact = create_test_committee_contact(
            "test-com-name1",
            "C00000000",
            self.committee.id,
            {
                "street_1": "test_sa1",
                "street_2": "test_sa2",
                "city": "test_c1",
                "state": "AL",
                "zip": "12345",
                "telephone": "555-555-5555",
                "country": "USA",
            },
        )
        self.test_org_contact = create_test_organization_contact(
            "test-org-name1",
            self.committee.id,
            {
                "street_1": "test_sa1",
                "street_2": "test_sa2",
                "city": "test_c1",
                "state": "AL",
                "zip": "12345",
                "telephone": "555-555-5555",
                "country": "USA",
            },
        )
        self.test_ind_contact = create_test_individual_contact(
            "test_ln1",
            "test_fn1",
            self.committee.id,
        )

        self.mock_request = Request(HttpRequest())
        self.mock_request.user = self.user
        self.mock_request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }

        self.transaction_serializer = TransactionSerializer(
            context={"request": self.mock_request},
        )

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

    def post_request(self, payload, params={}):
        request = self.factory.post(
            "/api/v1/transactions",
            json.dumps(payload, default=str),
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

    def delete_request(self, path="api/v1/transactions", params={}):
        request = self.factory.delete(path)
        request.user = self.user
        request.query_params = params
        request.data = {}
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        return request

    def get_request(self, path="api/v1/transactions", params={}):
        request = self.factory.get(path)
        request.user = self.user
        request.query_params = params
        request.data = {}
        request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }
        return request

    def test_save_transaction_pair(self):
        request = self.post_request(self.payloads["IN_KIND"])
        transaction = TransactionViewSet().save_transaction(request.data, request)
        self.assertEqual("John", transaction.contact_1.first_name)
        self.assertEqual("Smith", transaction.contact_1.last_name)

    def test_update(self):
        request = self.post_request(self.payloads["IN_KIND"])
        transaction = TransactionViewSet().save_transaction(request.data, request)
        updated_payload = deepcopy(self.payloads["IN_KIND"])
        updated_payload["id"] = str(transaction.id)
        updated_payload["contribution_amount"] = 999
        updated_payload["children"][0]["id"] = str(transaction.children[0].id)
        updated_payload["children"][0]["expenditure_amount"] = 999
        request = self.post_request(updated_payload)
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
        view_set.request = self.post_request({}, {"schedules": "A,B,C,C2,D,E"})
        self.assertEqual(view_set.get_queryset().count(), 13)
        view_set.request = self.post_request({}, {"schedules": "A,B,D,E"})
        self.assertEqual(view_set.get_queryset().count(), 11)
        view_set.request = self.post_request({}, {"schedules": ""})
        self.assertEqual(view_set.get_queryset().count(), 0)

    def test_get_previous_entity(self):
        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        view_set.request = self.post_request({}, {"contact_1_id": str(self.contact_1.id)})
        # leave out required params
        response = view_set.previous_transaction_by_entity(view_set.request)
        self.assertEqual(response.status_code, 400)

        response = view_set.previous_transaction_by_entity(
            self.post_request(
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
            self.post_request(
                {},
                {
                    "contact_1_id": str(self.contact_1.id),
                    "date": "2024-09-20",
                    "aggregation_group": "GENERAL_DISBURSEMENT",
                },
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_get_previous_entity_same_day(self):
        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        view_set.request = self.post_request({}, {"contact_1_id": str(self.contact_1.id)})

        first_transaction = create_schedule_a(
            "IND",
            self.committee,
            self.contact_3,
            "2023-01-12",
            "153.00",
        )

        second_transaction = create_schedule_a(
            "IND",
            self.committee,
            self.contact_3,
            "2023-01-12",
            "47.00",
        )

        self.assertGreater(second_transaction.created, first_transaction.created)

        response = view_set.previous_transaction_by_entity(
            self.post_request(
                {},
                {
                    "transaction_id": str(second_transaction.id),
                    "contact_1_id": str(self.contact_3.id),
                    "date": "2023-01-12",
                    "aggregation_group": "GENERAL",
                },
            )
        )
        self.assertEqual(response.data["id"], str(first_transaction.id))

        response = view_set.previous_transaction_by_entity(
            self.post_request(
                {},
                {
                    "transaction_id": first_transaction.id,
                    "contact_1_id": str(self.contact_3.id),
                    "date": "2023-01-12",
                    "aggregation_group": "GENERAL",
                },
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_get_entity_date_leapfrogging(self):
        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        view_set.request = self.post_request({}, {"contact_1_id": str(self.contact_1.id)})

        first_transaction = create_schedule_a(
            "IND",
            self.committee,
            self.contact_3,
            "2023-01-12",
            "153.00",
        )

        second_transaction = create_schedule_a(
            "IND",
            self.committee,
            self.contact_3,
            "2023-01-12",
            "47.00",
        )

        response = view_set.previous_transaction_by_entity(
            self.post_request(
                {},
                {
                    "transaction_id": first_transaction.id,
                    "contact_1_id": str(self.contact_3.id),
                    "date": "2023-01-15",
                    "aggregation_group": "GENERAL",
                },
            )
        )
        self.assertEqual(response.data["id"], str(second_transaction.id))
        self.assertEqual(response.data["aggregate"], "47.00")

        transaction_data = {
            **self.transaction_serializer.to_representation(first_transaction),
            **{
                "contribution_date": "2023-01-15",
                "schedule_id": "A",
                "schema_name": "INDIVIDUAL_RECEIPT",
                "transaction_type_identifier": "INDIVIDUAL_RECEIPT",
            },
        }

        view_set.save_transaction(transaction_data, view_set.request)

        saved_transaction = view_set.get_queryset().get(id=first_transaction.id)
        self.assertEqual(str(saved_transaction.aggregate), "200.00")

    def test_get_entity_date_leapfrogging_and_contact_change(self):
        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        view_set.request = self.post_request({}, {"contact_1_id": str(self.contact_1.id)})

        first_transaction = create_schedule_a(
            "IND",
            self.committee,
            self.contact_3,
            "2023-01-12",
            "153.00",
        )

        second_transaction = create_schedule_a(
            "IND",
            self.committee,
            self.contact_3,
            "2023-01-15",
            "47.00",
        )

        third_transaction = create_schedule_a(
            "IND",
            self.committee,
            self.contact_2,
            "2023-01-20",
            "25.00",
        )

        first_transaction.contact_1 = self.contact_2

        transaction_data = {
            **self.transaction_serializer.to_representation(first_transaction),
            **{
                "contribution_date": "2023-01-18",
                "schedule_id": "A",
                "schema_name": "INDIVIDUAL_RECEIPT",
                "transaction_type_identifier": "INDIVIDUAL_RECEIPT",
                "contributor_street_1": "Test",
                "contributor_city": "Testville",
                "contributor_state": "IL",
                "contributor_zip": "12345",
            },
        }

        view_set.save_transaction(transaction_data, view_set.request)

        first_transaction.refresh_from_db()
        second_transaction.refresh_from_db()
        third_transaction.refresh_from_db()

        self.assertEqual(str(first_transaction.aggregate), "153.00")
        self.assertEqual(str(second_transaction.aggregate), "47.00")
        self.assertEqual(str(third_transaction.aggregate), "178.00")

    def test_get_entity_move_date_backwards(self):
        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        view_set.request = self.post_request({}, {"contact_1_id": str(self.contact_1.id)})

        first_transaction = create_schedule_a(
            "IND",
            self.committee,
            self.contact_3,
            "2023-01-12",
            "153.00",
        )

        second_transaction = create_schedule_a(
            "IND",
            self.committee,
            self.contact_3,
            "2023-01-15",
            "47.00",
        )

        third_transaction = create_schedule_a(
            "IND",
            self.committee,
            self.contact_3,
            "2023-01-18",
            "25.00",
        )

        response = view_set.previous_transaction_by_entity(
            self.post_request(
                {},
                {
                    "transaction_id": first_transaction.id,
                    "contact_1_id": str(self.contact_3.id),
                    "date": "2023-01-15",
                    "aggregation_group": "GENERAL",
                },
            )
        )
        self.assertEqual(response.status_code, 404)

        transaction_data = {
            **self.transaction_serializer.to_representation(third_transaction),
            **{
                "contribution_date": "2023-01-10",
                "schedule_id": "A",
                "schema_name": "INDIVIDUAL_RECEIPT",
                "transaction_type_identifier": "INDIVIDUAL_RECEIPT",
            },
        }

        view_set.save_transaction(transaction_data, view_set.request)

        saved_transaction = view_set.get_queryset().get(id=first_transaction.id)
        self.assertEqual(str(saved_transaction.aggregate), "178.00")
        response = view_set.previous_transaction_by_entity(
            self.post_request(
                {},
                {
                    "transaction_id": first_transaction.id,
                    "contact_1_id": str(self.contact_3.id),
                    "date": "2023-01-15",
                    "aggregation_group": "GENERAL",
                },
            )
        )
        self.assertEqual(response.data["id"], str(third_transaction.id))

        first_transaction.refresh_from_db()
        second_transaction.refresh_from_db()
        third_transaction.refresh_from_db()

        self.assertEqual(str(first_transaction.aggregate), "178.00")
        self.assertEqual(str(second_transaction.aggregate), "225.00")
        self.assertEqual(str(third_transaction.aggregate), "25.00")

    def test_get_previous_election(self):
        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        view_set.request = self.post_request(
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
        view_set.request = self.post_request(
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

        view_set.request = self.post_request(
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

        self.assertEqual(transaction.get("date"), "2023-01-22")

    def test_get_previous_election_leapfrogging(self):
        view_set = TransactionViewSet()
        view_set.format_kwarg = {}

        view_set.request = self.post_request(
            {},
            {
                "transaction_id": self.transaction.id,
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

        self.assertEqual(transaction.get("date"), "2023-01-22")
        self.assertEqual(transaction.get("calendar_ytd_per_election_office"), "147.00")

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
        response = view_set.save_reatt_redes_transactions(self.post_request(payload))
        transactions = response.data
        self.assertEqual(len(transactions), 2)

    def test_add_transaction_to_report(self):
        report_id = str(self.q1_report.id)
        transaction_id = str(self.transaction.id)

        payload = {"transaction_id": transaction_id, "report_id": report_id}
        view_set = TransactionViewSet()
        response = view_set.add_transaction_to_report(self.post_request(payload))

        expected_data = f"Transaction(s) added to report: [UUID('{transaction_id}')]"
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

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
        response = view_set.add_transaction_to_report(self.post_request(payload))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, "No transaction matching id provided")

        # Verify response when non existing report id provided
        payload["transaction_id"] = str(self.transaction.id)
        payload["report_id"] = "474a1a10-da68-4d71-9a11-cccccccccccc"
        response = view_set.add_transaction_to_report(self.post_request(payload))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, "No report matching id provided")

    def test_add_transaction_family_to_report_from_parent(self):
        jf_transfer = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="500.00",
            itemized=True,
            report=self.q1_report,
        )
        jf_transfer.save()

        partnership_jf_transfer_memo = create_schedule_a(
            "PARTNERSHIP_JF_TRANSFER_MEMO",
            self.committee,
            self.contact_1,
            "2024-01-02",
            amount="50.00",
            itemized=True,
            report=self.q1_report,
        )
        partnership_jf_transfer_memo.parent_transaction = jf_transfer
        partnership_jf_transfer_memo.save()

        transaction_id = str(jf_transfer.id)
        report_id = str(self.q2_report.id)
        payload = {"transaction_id": transaction_id, "report_id": report_id}
        view_set = TransactionViewSet()
        view_set.add_transaction_to_report(self.post_request(payload))

        self.assertIn(self.q2_report, jf_transfer.reports.all())
        self.assertIn(self.q2_report, partnership_jf_transfer_memo.reports.all())

    def test_add_transaction_family_to_report_from_child(self):
        jf_transfer = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.contact_1,
            "2024-01-01",
            amount="500.00",
            itemized=True,
            report=self.q1_report,
        )
        jf_transfer.save()

        partnership_jf_transfer_memo = create_schedule_a(
            "PARTNERSHIP_JF_TRANSFER_MEMO",
            self.committee,
            self.contact_1,
            "2024-01-02",
            amount="50.00",
            itemized=True,
            report=self.q1_report,
        )
        partnership_jf_transfer_memo.parent_transaction = jf_transfer
        partnership_jf_transfer_memo.save()

        transaction_id = str(partnership_jf_transfer_memo.id)
        report_id = str(self.q2_report.id)
        payload = {"transaction_id": transaction_id, "report_id": report_id}
        view_set = TransactionViewSet()
        view_set.add_transaction_to_report(self.post_request(payload))

        self.assertIn(self.q2_report, jf_transfer.reports.all())
        self.assertIn(self.q2_report, partnership_jf_transfer_memo.reports.all())

    def test_remove_transaction_from_report(self):
        report_id = str(self.q1_report.id)
        transaction_id = str(self.transaction.id)

        payload = {"transaction_id": transaction_id, "report_id": report_id}
        view_set = TransactionViewSet()
        response = view_set.remove_transaction_from_report(self.post_request(payload))

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
        response = view_set.remove_transaction_from_report(self.post_request(payload))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, "No transaction matching id provided")

        # Verify response when non existing report id provided
        payload["transaction_id"] = str(self.transaction.id)
        payload["report_id"] = "474a1a10-da68-4d71-9a11-cccccccccccc"
        response = view_set.remove_transaction_from_report(self.post_request(payload))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, "No report matching id provided")

    def test_save_debt(self):
        payload = self.payloads["DEBT"]
        payload["report_ids"] = [str(self.q1_report.id)]
        view_set = TransactionViewSet()
        response = view_set.create(self.post_request(payload))
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
        request = self.delete_request(f"api/v1/transactions/{self.transaction.id}/")
        force_authenticate(request, self.user)
        response = TransactionViewSet.as_view({"delete": "destroy"})(
            request, pk=self.transaction.id
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Transaction.objects.filter(pk=self.transaction.pk).exists())

    def test_destroy_with_dependent_parent(self):
        jf_transfer = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.contact_1,
            "2020-01-01",
            "100",
        )
        partnership_memo = create_schedule_a(
            "PARTNERSHIP_JF_TRANSFER_MEMO",
            self.committee,
            self.contact_1,
            "2023-01-01",
            "100",
            parent_id=jf_transfer.id,
        )
        partnership_memo.schedule_a.contribution_purpose_descrip = (
            "JF Memo: None (See Partnership Attribution(s) below)"
        )
        partnership_memo.schedule_a.save()
        partnership_attribution_memo = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
            self.committee,
            self.contact_1,
            "2023-01-01",
            "100",
            parent_id=partnership_memo.id,
        )
        get_request = self.get_request(f"api/v1/transactions/{partnership_memo.id}/")
        force_authenticate(get_request, self.user)
        response = TransactionViewSet.as_view({"get": "retrieve"})(
            get_request, pk=partnership_memo.id
        )
        self.assertEqual(
            response.data["contribution_purpose_descrip"],
            "JF Memo: None (See Partnership Attribution(s) below)",
        )

        # If we delete the attribution memo, the parent memo should be updated
        delete_request = self.delete_request(
            f"api/v1/transactions/{partnership_attribution_memo.id}/"
        )
        force_authenticate(delete_request, self.user)
        response = TransactionViewSet.as_view({"delete": "destroy"})(
            delete_request, pk=partnership_attribution_memo.id
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = TransactionViewSet.as_view({"get": "retrieve"})(
            get_request, pk=partnership_memo.id
        )
        self.assertEqual(
            response.data["contribution_purpose_descrip"],
            "JF Memo: None (Partnership attributions do not meet itemization threshold)",
        )

    def test_delete_carried_forward_loan_on_repayment_to_orignal_loan(self):
        """Paying off a loan in the original report should delete any carried forward
        copies in future reports"""
        # create q1 and associated loan
        q1_report = create_form3x(self.committee, "2025-01-01", "2025-03-31", {})
        original_loan = create_loan(
            self.committee,
            self.test_ind_contact,
            "1000.00",
            "2025-12-31",
            "6%",
            form_type="SC/10",
            loan_incurred_date="2025-01-01",
            report=q1_report,
        )
        create_schedule_b(
            "LOAN_REPAYMENT_MADE",
            self.committee,
            self.test_ind_contact,
            "2025-01-02",
            "100.00",
            loan_id=original_loan.id,
            report=q1_report,
        )

        # create q2 and confirm loan carry forward
        q2_report = create_form3x(self.committee, "2025-04-01", "2025-06-30", {})
        q2_carried_over_loan = (
            Transaction.objects.transaction_view()
            .filter(reports__id=q2_report.id, loan_id=original_loan.id)
            .get()
        )
        self.assertEqual(q2_carried_over_loan.loan_balance, 900.00)

        # create q3 and confirm loan carry forward
        q3_report = create_form3x(self.committee, "2025-07-01", "2025-09-30", {})
        q3_carried_over_loan = (
            Transaction.objects.transaction_view()
            .filter(reports__id=q3_report.id, loan_id=original_loan.id)
            .get()
        )
        self.assertEqual(q3_carried_over_loan.loan_balance, 900.00)

        # make a repayment in q1 and confirm q2 and q3 carry forward loans are deleted
        q1_loan_repayment = self.create_loan_repayment_payload(
            original_loan,
            q1_report,
            "2025-01-03",
            900.00,
        )
        response = TransactionViewSet().create(self.post_request(q1_loan_repayment))
        self.assertEqual(response.status_code, 200)

        # confirm q2 and q3 carry forward loans are deleted
        self.assertTrue(Transaction.all_objects.get(id=q2_carried_over_loan.id).deleted)
        self.assertTrue(Transaction.all_objects.get(id=q3_carried_over_loan.id).deleted)

    def test_delete_carried_forward_loan_on_repayment_to_carried_forward_loan(self):
        """Paying off a loan in one report should delete any carried forward
        copies in future reports"""
        # create q1 and associated loan
        test_q1_report_2025 = create_form3x(
            self.committee, "2025-01-01", "2025-03-31", {}
        )
        test_loan = create_loan(
            self.committee,
            self.test_ind_contact,
            "1000.00",
            "2025-12-31",
            "6%",
            form_type="SC/10",
            loan_incurred_date="2025-01-01",
            report=test_q1_report_2025,
        )
        create_schedule_b(
            "LOAN_REPAYMENT_MADE",
            self.committee,
            self.test_ind_contact,
            "2025-01-02",
            "100.00",
            loan_id=test_loan.id,
            report=test_q1_report_2025,
        )

        # create q2 and confirm loan carry forward
        test_q2_report_2025 = create_form3x(
            self.committee, "2025-04-01", "2025-06-30", {}
        )
        test_q2_carried_over_loan = (
            Transaction.objects.transaction_view()
            .filter(reports__id=test_q2_report_2025.id, loan_id=test_loan.id)
            .get()
        )
        self.assertEqual(test_q2_carried_over_loan.loan_balance, 900.00)

        # make repayment in q2
        create_schedule_b(
            "LOAN_REPAYMENT_MADE",
            self.committee,
            self.test_ind_contact,
            "2025-04-02",
            "150.00",
            loan_id=test_q2_carried_over_loan.id,
            report=test_q2_report_2025,
        )

        # create q3 and confirm loan carry forward
        test_q3_report_2025 = create_form3x(
            self.committee, "2025-07-01", "2025-09-30", {}
        )
        test_q3_carried_over_loan = (
            Transaction.objects.transaction_view()
            .filter(reports__id=test_q3_report_2025.id, loan_id=test_loan.id)
            .get()
        )
        self.assertEqual(test_q3_carried_over_loan.loan_balance, 750.00)

        # pay off loan on q2 and confirm q3 carry foward loan deleted
        test_q2_final_loan_repayment = self.create_loan_repayment_payload(
            test_q2_carried_over_loan,
            test_q2_report_2025,
            "2025-04-03",
            750.00,
        )
        response = TransactionViewSet().create(
            self.post_request(test_q2_final_loan_repayment)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Transaction.objects.transaction_view()
            .get(pk=test_q2_carried_over_loan.id)
            .loan_balance,
            0.00,
        )
        self.assertIsNotNone(
            Transaction.all_objects.get(pk=test_q3_carried_over_loan.id).deleted
        )
        self.assertIsNone(
            Transaction.all_objects.get(pk=test_q2_carried_over_loan.id).deleted
        )

    def test_delete_carried_forward_debt_on_repayment_to_orignal_debt(self):
        """Paying off a debt in the original report should delete any carried forward
        copies in future reports"""
        # create q1 and associated debt
        q1_report = create_form3x(self.committee, "2025-01-01", "2025-03-31", {})
        original_debt = create_debt(
            self.committee,
            self.test_org_contact,
            "1000.00",
            report=q1_report,
        )
        create_schedule_b(
            "OPERATING_EXPENDITURE_CREDIT_CARD_PAYMENT",
            self.committee,
            self.test_org_contact,
            "2025-01-02",
            Decimal("100.00"),
            debt_id=original_debt.id,
            report=q1_report,
        )

        # create q2 and confirm debt carry forward
        q2_report = create_form3x(self.committee, "2025-04-01", "2025-06-30", {})
        q2_carried_over_debt = (
            Transaction.objects.transaction_view()
            .filter(reports__id=q2_report.id, debt_id=original_debt.id)
            .get()
        )
        self.assertEqual(q2_carried_over_debt.balance_at_close, 900.00)

        # create q3 and confirm debt carry forward
        q3_report = create_form3x(self.committee, "2025-07-01", "2025-09-30", {})
        q3_carried_over_debt = (
            Transaction.objects.transaction_view()
            .filter(reports__id=q3_report.id, debt_id=original_debt.id)
            .get()
        )
        self.assertEqual(q3_carried_over_debt.balance_at_close, 900.00)

        # make a repayment in q1 and confirm q2 and q3 carry forward debts are deleted
        q1_debt_repayment = self.create_debt_repayment_payload(
            original_debt,
            q1_report,
            "2025-01-03",
            900.00,
        )
        response = TransactionViewSet().create(self.post_request(q1_debt_repayment))
        self.assertEqual(response.status_code, 200)

        # confirm q2 and q3 carry forward debts are deleted
        self.assertTrue(Transaction.all_objects.get(id=q2_carried_over_debt.id).deleted)
        self.assertTrue(Transaction.all_objects.get(id=q3_carried_over_debt.id).deleted)

    def test_delete_carried_forward_debt_on_repayment_to_carried_forward_debt(self):
        """Paying off a debt in one report should delete any carried forward
        copies in future reports"""
        # create q1 and associated debt
        test_q1_report_2025 = create_form3x(
            self.committee, "2025-01-01", "2025-03-31", {}
        )
        test_debt = create_debt(
            self.committee,
            self.test_org_contact,
            "1500.00",
            report=test_q1_report_2025,
        )
        create_schedule_b(
            "OPERATING_EXPENDITURE_CREDIT_CARD_PAYMENT",
            self.committee,
            self.test_org_contact,
            "2025-01-02",
            Decimal("400.00"),
            debt_id=test_debt.id,
            report=test_q1_report_2025,
        )

        # create q2 and confirm debt carry forward
        test_q2_report_2025 = create_form3x(
            self.committee, "2025-04-01", "2025-06-30", {}
        )
        test_q2_carried_over_debt = (
            Transaction.objects.transaction_view()
            .filter(reports__id=test_q2_report_2025.id, debt_id=test_debt.id)
            .get()
        )
        self.assertEqual(test_q2_carried_over_debt.balance_at_close, Decimal(1100.00))

        # make repayment in q2
        create_schedule_b(
            "OPERATING_EXPENDITURE_CREDIT_CARD_PAYMENT",
            self.committee,
            self.test_org_contact,
            "2025-04-02",
            "300.00",
            debt_id=test_q2_carried_over_debt.id,
            report=test_q2_report_2025,
        )

        # create q3 and confirm debt carry forward
        test_q3_report_2025 = create_form3x(
            self.committee, "2025-07-01", "2025-09-30", {}
        )
        test_q3_carried_over_debt = (
            Transaction.objects.transaction_view()
            .filter(reports__id=test_q3_report_2025.id, debt_id=test_debt.id)
            .get()
        )
        self.assertEqual(test_q3_carried_over_debt.balance_at_close, 800.00)

        # pay off debt on q2 and confirm q3 carry foward debt deleted
        test_q2_final_debt_repayment = self.create_debt_repayment_payload(
            test_q2_carried_over_debt,
            test_q2_report_2025,
            "2025-04-03",
            800.00,
        )
        response = TransactionViewSet().create(
            self.post_request(test_q2_final_debt_repayment)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Transaction.objects.transaction_view()
            .get(pk=test_q2_carried_over_debt.id)
            .balance_at_close,
            0.00,
        )
        self.assertIsNotNone(
            Transaction.all_objects.get(pk=test_q3_carried_over_debt.id).deleted
        )
        self.assertIsNone(
            Transaction.all_objects.get(pk=test_q2_carried_over_debt.id).deleted
        )

    def test_create_schedule_f_debt_repayment(self):
        """Making a schedule f debt repayment should reduce the balance accordingly"""
        # create q1 and associated debt
        test_q1_report_2025 = create_form3x(
            self.committee, "2025-01-01", "2025-03-31", {}
        )
        test_debt = create_debt(
            self.committee,
            self.test_org_contact,
            "1000.00",
            report=test_q1_report_2025,
        )
        # pay off debt on q2 and confirm q3 carry foward debt deleted
        test_schedule_f_debt_repayment = self.create_schedule_f_debt_repayment_payload(
            test_debt,
            test_q1_report_2025,
            "2025-04-03",
            150.00,
        )
        response = self.view.create(
            self.post_request(test_schedule_f_debt_repayment)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            Transaction.objects.transaction_view().get(pk=test_debt.id).balance_at_close,
            850.00,
        )

    def create_loan_repayment_payload(
        self,
        loan: Transaction,
        report: Report,
        repayment_date: str,
        repayment_amount: int,
    ):
        loan_representation = self.transaction_serializer.to_representation(loan)
        loan_repayment_payload = deepcopy(self.payloads["LOAN_REPAYMENT"])
        loan_repayment_payload["contact_1"] = loan_representation["contact_1"]
        loan_repayment_payload["contact_1_id"] = loan_representation["contact_1_id"]
        loan_repayment_payload["loan"] = loan_representation
        loan_repayment_payload["loan_id"] = loan_representation["id"]
        loan_repayment_payload["report_ids"] = [str(report.id)]
        loan_repayment_payload["expenditure_date"] = repayment_date
        loan_repayment_payload["expenditure_amount"] = repayment_amount
        return loan_repayment_payload

    def create_debt_repayment_payload(
        self,
        debt: Transaction,
        report: Report,
        repayment_date: str,
        repayment_amount: int,
    ):
        debt_representation = self.transaction_serializer.to_representation(debt)
        debt_repayment_payload = deepcopy(self.payloads["DEBT_REPAYMENT"])
        debt_repayment_payload["contact_1"] = debt_representation["contact_1"]
        debt_repayment_payload["contact_1_id"] = debt_representation["contact_1_id"]
        debt_repayment_payload["debt"] = debt_representation
        debt_repayment_payload["debt_id"] = debt_representation["id"]
        debt_repayment_payload["report_ids"] = [str(report.id)]
        debt_repayment_payload["expenditure_date"] = repayment_date
        debt_repayment_payload["expenditure_amount"] = repayment_amount
        return debt_repayment_payload

    def create_schedule_f_debt_repayment_payload(
        self,
        debt: Transaction,
        report: Report,
        repayment_date: str,
        repayment_amount: int,
    ):
        debt_representation = self.transaction_serializer.to_representation(debt)
        schedule_f_debt_repayment_payload = deepcopy(
            self.payloads["COORDINATED_PARTY_EXPENDITURE"]
        )
        schedule_f_debt_repayment_payload["contact_1"] = debt_representation["contact_1"]
        schedule_f_debt_repayment_payload["contact_1_id"] = debt_representation[
            "contact_1_id"
        ]
        schedule_f_debt_repayment_payload["debt"] = debt_representation
        schedule_f_debt_repayment_payload["debt_id"] = debt_representation["id"]
        schedule_f_debt_repayment_payload["report_ids"] = [str(report.id)]
        schedule_f_debt_repayment_payload["expenditure_date"] = repayment_date
        schedule_f_debt_repayment_payload["expenditure_amount"] = repayment_amount
        return schedule_f_debt_repayment_payload

    def test_schedule_f_aggregation(self):
        report = create_form3x(
            self.committee, "2023-01-01", "2023-03-31", {}, report_code="Q1"
        )
        contact_org = create_test_organization_contact(
            "Testerson Inc.",
            self.committee.id,
            {
                "city": "Testville",
                "country": "USA",
                "state": "AK",
                "street_1": "1234 Test Ln",
                "street_2": None,
                "telephone": None,
                "zip": "12345"
            }
        )
        contact_can = create_test_candidate_contact(
            "Testerson",
            "Philip",
            self.committee.id,
            "S6MT00162",
            "S",
            "MT",
            None,
            {
                "city": "HELENA",
                "country": "USA",
                "employer": None,
                "middle_name": None,
                "occupation": None,
                "prefix": None,
                "state": "MT",
                "street_1": "PO BOX 1135",
                "street_2": None,
                "suffix": None,
                "telephone": None,
                "zip": "59624"
            }
        )
        contact_com = create_test_committee_contact(
            "Testersons United",
            "C12344321",
            self.committee.id,
            {
                "city": "BILLINGS",
                "country": "USA",
                "state": "MT",
                "street_1": "PO BOX 558",
                "telephone": "+1 3144010501",
                "zip": "59103"
            }
        )
        self.view.request.query_params["report_id"] = report.id

        a = create_schedule_f(
            type="COORDINATED_PARTY_EXPENDITURE",
            committee=self.committee,
            contact_1=contact_org,
            contact_2=contact_can,
            contact_3=contact_com,
            report=report,
            schedule_data={
                "expenditure_amount": 125.00,
                "expenditure_date": "2023-02-11",
                "general_election_year": "2024"
            }
        )
        b = create_schedule_f(
            type="COORDINATED_PARTY_EXPENDITURE",
            committee=self.committee,
            contact_1=contact_org,
            contact_2=contact_can,
            contact_3=contact_com,
            report=report,
            schedule_data={
                "expenditure_amount": 75.00,
                "expenditure_date": "2023-02-15",
                "general_election_year": "2024"
            }
        )

        trans_a = Transaction.objects.get(id=a.id)
        trans_b = Transaction.objects.get(id=b.id)

        self.assertEqual(trans_a.schedule_f.general_election_year, "2024")
        self.assertEqual(trans_a.schedule_f.expenditure_amount, 125.00)

        self.view.process_general_election_year_aggregates(trans_a)

        trans_b.refresh_from_db()
        self.assertEqual(trans_b.schedule_f.aggregate_general_elec_expended, 200.00)

    def test_schedule_f_aggregation_edge_cases(self):
        report = create_form3x(
            self.committee, "2023-01-01", "2023-03-31", {}, report_code="Q1"
        )
        contact_org = create_test_organization_contact(
            "Testerson Inc.",
            self.committee.id,
            {
                "city": "Testville",
                "country": "USA",
                "state": "AK",
                "street_1": "1234 Test Ln",
                "street_2": None,
                "telephone": None,
                "zip": "12345"
            }
        )
        contact_can = create_test_candidate_contact(
            "Testerson",
            "Philip",
            self.committee.id,
            "S6MT00162",
            "S",
            "MT",
            None,
            {
                "city": "HELENA",
                "country": "USA",
                "employer": None,
                "middle_name": None,
                "occupation": None,
                "prefix": None,
                "state": "MT",
                "street_1": "PO BOX 1135",
                "street_2": None,
                "suffix": None,
                "telephone": None,
                "zip": "59624"
            }
        )
        contact_com = create_test_committee_contact(
            "Testersons United",
            "C12344321",
            self.committee.id,
            {
                "city": "BILLINGS",
                "country": "USA",
                "state": "MT",
                "street_1": "PO BOX 558",
                "telephone": "+1 3144010501",
                "zip": "59103"
            }
        )

        transaction_1_data = gen_schedule_f_request_data(
            str(report.id),
            "153.00",
            "2024-01-12",
            "2022",
            contact_org,
            contact_can,
            contact_com
        )
        transaction_2_data = gen_schedule_f_request_data(
            str(report.id),
            "47.00",
            "2024-01-13",
            "2022",
            contact_org,
            contact_can,
            contact_com
        )

        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        view_set.request = self.post_request(transaction_1_data)

        # Test standard aggregation
        transaction_1 = view_set.save_transaction(transaction_1_data, view_set.request)
        transaction_2 = view_set.save_transaction(transaction_2_data, view_set.request)

        self.assertEqual(transaction_1.schedule_f.aggregate_general_elec_expended, 153.00)
        self.assertEqual(transaction_2.schedule_f.aggregate_general_elec_expended, 200.00)

        # Test leapfrogging forward
        move_transaction_1_data = {
            **transaction_1_data,
            "expenditure_date": "2024-01-15",
            "id": transaction_1.id
        }

        transaction_1 = view_set.save_transaction(
            move_transaction_1_data,
            view_set.request
        )
        transaction_2.refresh_from_db()

        self.assertEqual(transaction_1.schedule_f.aggregate_general_elec_expended, 200.00)
        self.assertEqual(transaction_2.schedule_f.aggregate_general_elec_expended, 47.00)

        # Test leapfrogging backward
        move_transaction_1_again_data = {
            **move_transaction_1_data,
            "expenditure_date": "2024-01-10",
        }

        transaction_1 = view_set.save_transaction(
            move_transaction_1_again_data,
            view_set.request
        )
        transaction_2.refresh_from_db()

        self.assertEqual(transaction_1.schedule_f.aggregate_general_elec_expended, 153.00)
        self.assertEqual(transaction_2.schedule_f.aggregate_general_elec_expended, 200.00)

        # Test change GE year
        change_ge_transaction_1_data = {
            **move_transaction_1_again_data,
            "general_election_year": "1999",
        }

        transaction_1 = view_set.save_transaction(
            change_ge_transaction_1_data,
            view_set.request
        )
        transaction_2.refresh_from_db()

        self.assertEqual(transaction_1.schedule_f.aggregate_general_elec_expended, 153.00)
        self.assertEqual(transaction_2.schedule_f.aggregate_general_elec_expended, 47.00)

        # Test change GE year back
        change_ge_transaction_1_back_data = {
            **move_transaction_1_again_data,
            "general_election_year": "2022",
        }

        transaction_1 = view_set.save_transaction(
            change_ge_transaction_1_back_data,
            view_set.request
        )
        transaction_2.refresh_from_db()

        self.assertEqual(transaction_1.schedule_f.aggregate_general_elec_expended, 153.00)
        self.assertEqual(transaction_2.schedule_f.aggregate_general_elec_expended, 200.00)

    def test_previous_transaction_by_payee_candidate(self):
        report = create_form3x(
            self.committee, "2023-01-01", "2023-03-31", {}, report_code="Q1"
        )
        contact_org = create_test_organization_contact(
            "Testerson Inc.",
            self.committee.id,
            {
                "city": "Testville",
                "country": "USA",
                "state": "AK",
                "street_1": "1234 Test Ln",
                "street_2": None,
                "telephone": None,
                "zip": "12345"
            }
        )
        contact_can = create_test_candidate_contact(
            "Testerson",
            "Philip",
            self.committee.id,
            "S6MT00162",
            "S",
            "MT",
            None,
            {
                "city": "HELENA",
                "country": "USA",
                "employer": None,
                "middle_name": None,
                "occupation": None,
                "prefix": None,
                "state": "MT",
                "street_1": "PO BOX 1135",
                "street_2": None,
                "suffix": None,
                "telephone": None,
                "zip": "59624"
            }
        )
        contact_com = create_test_committee_contact(
            "Testersons United",
            "C12344321",
            self.committee.id,
            {
                "city": "BILLINGS",
                "country": "USA",
                "state": "MT",
                "street_1": "PO BOX 558",
                "telephone": "+1 3144010501",
                "zip": "59103"
            }
        )

        transaction_1_data = gen_schedule_f_request_data(
            str(report.id),
            "153.00",
            "2024-01-12",
            "2022",
            contact_org,
            contact_can,
            contact_com
        )
        transaction_2_data = gen_schedule_f_request_data(
            str(report.id),
            "47.00",
            "2024-01-13",
            "2022",
            contact_org,
            contact_can,
            contact_com
        )

        view_set = TransactionViewSet()
        view_set.format_kwarg = {}
        view_set.request = self.post_request(transaction_1_data)

        # Test standard aggregation
        transaction_1 = view_set.save_transaction(transaction_1_data, view_set.request)
        transaction_2 = view_set.save_transaction(transaction_2_data, view_set.request)

        response = view_set.previous_transaction_by_payee_candidate(
            self.post_request(
                {},
                {
                    "contact_2_id": str(contact_can.id),
                    "date": "2024-01-10",
                    "aggregation_group": "COORDINATED_PARTY_EXPENDITURES",
                    "general_election_year": "2022"
                },
            )
        )
        self.assertEqual(response.status_code, 404)

        response = view_set.previous_transaction_by_payee_candidate(
            self.post_request(
                {},
                {
                    "contact_2_id": str(contact_can.id),
                    "date": "2024-01-12",
                    "aggregation_group": "COORDINATED_PARTY_EXPENDITURES",
                    "general_election_year": "2022"
                },
            )
        )
        self.assertEqual(response.data["id"], str(transaction_1.id))

        response = view_set.previous_transaction_by_payee_candidate(
            self.post_request(
                {},
                {
                    "contact_2_id": str(contact_can.id),
                    "date": "2024-01-13",
                    "aggregation_group": "COORDINATED_PARTY_EXPENDITURES",
                    "general_election_year": "2022"
                },
            )
        )
        self.assertEqual(response.data["id"], str(transaction_2.id))

        response = view_set.previous_transaction_by_payee_candidate(
            self.post_request(
                {},
                {
                    "contact_2_id": str(contact_can.id),
                    "date": "2024-01-15",
                    "aggregation_group": "COORDINATED_PARTY_EXPENDITURES",
                    "general_election_year": "2020"
                },
            )
        )
        self.assertEqual(response.status_code, 404)

        response = view_set.previous_transaction_by_payee_candidate(
            self.post_request(
                {},
                {
                    "contact_2_id": str(contact_com.id),
                    "date": "2024-01-15",
                    "aggregation_group": "COORDINATED_PARTY_EXPENDITURES",
                    "general_election_year": "2022"
                },
            )
        )
        self.assertEqual(response.status_code, 404)

        response = view_set.previous_transaction_by_payee_candidate(
            self.post_request(
                {},
                {
                    "contact_2_id": str(contact_can.id),
                    "date": "2024-01-15",
                    "aggregation_group": "THIS_DOESNT_MATCH_ANYTHING",
                    "general_election_year": "2022"
                },
            )
        )
        self.assertEqual(response.status_code, 404)
