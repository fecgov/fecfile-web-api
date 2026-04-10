from django.test import TestCase
from fecfiler.user.models import User
from rest_framework.request import HttpRequest, Request
from fecfiler.transactions.serializers import (
    TransactionSerializer,
    REDESIGNATION_TO,
    REATTRIBUTION_TO,
    REATTRIBUTED,
    REDESIGNATED,
)
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.transactions.tests.utils import (
    create_schedule_a,
    create_schedule_b,
    create_schedule_f,
    create_loan_from_bank,
)
from fecfiler.reports.tests.utils import create_form3x


class TransactionSerializerBaseTestCase(TestCase):

    def setUp(self):
        self.missing_type_transaction = {}
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        self.user = User.objects.create(email="test@fec.gov", username="gov")
        self.mock_request = Request(HttpRequest())
        self.mock_request.user = self.user
        self.mock_request.session = {
            "committee_uuid": str(self.committee.id),
            "committee_id": str(self.committee.committee_id),
        }

    def test_no_transaction_type_identifier(self):
        serializer = TransactionSerializer(
            data=self.missing_type_transaction,
            context={"request": self.mock_request},
        )

        self.assertEqual(
            serializer.get_schema_name({"schema_name": "INDIVIDUAL_RECEIPT"}),
            "INDIVIDUAL_RECEIPT",
        )

    def test_no_reattribution(self):
        transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT", self.committee, None, None, 1
        )

        serializer = TransactionSerializer(
            context={"request": self.mock_request},
        )
        representation = serializer.to_representation(transaction)
        self.assertIsNone(representation.get("reatt_redes_total"))

        transaction.schedule_a.reattribution_redesignation_tag = REATTRIBUTED

        representation = serializer.to_representation(transaction)
        self.assertEqual(representation.get("reatt_redes_total"), "0.0")

    def test_has_reattribution(self):
        transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT", self.committee, None, None, 1
        )
        transaction.schedule_a.reattribution_redesignation_tag = REATTRIBUTED
        reatttribution = create_schedule_a(
            "INDIVIDUAL_RECEIPT", self.committee, None, None, 1
        )
        reatttribution.reatt_redes = transaction
        reatttribution.schedule_a.reattribution_redesignation_tag = REATTRIBUTION_TO
        reatttribution.schedule_a.save()
        reatttribution.save()
        serializer = TransactionSerializer(
            context={"request": self.mock_request},
        )
        representation = serializer.to_representation(transaction)
        self.assertEqual(representation.get("reatt_redes_total"), "1.00")

    def test_has_redesignation(self):
        transaction = create_schedule_b(
            "OPERATING_EXPENDITURE", self.committee, None, None, 1
        )
        transaction.schedule_b.reattribution_redesignation_tag = REDESIGNATED
        redesignation = create_schedule_b(
            "OPERATING_EXPENDITURE", self.committee, None, None, 1
        )
        redesignation.reatt_redes = transaction
        redesignation.schedule_b.reattribution_redesignation_tag = REDESIGNATION_TO
        redesignation.schedule_b.save()
        redesignation.save()
        serializer = TransactionSerializer(
            context={"request": self.mock_request},
        )
        representation = serializer.to_representation(transaction)
        self.assertEqual(representation.get("reatt_redes_total"), "1.00")

    def test_schedule_f_serialization(self):
        create_schedule_f(
            "COORDINATED_PARTY_EXPENDITURE",
            self.committee,
            None,
            None,
            None,
            None,
            None,
            schedule_data={
                "expenditure_date": "2024-01-09",
                "expenditure_amount": 22,
            }
        )

        transaction = create_schedule_f(
            "COORDINATED_PARTY_EXPENDITURE",
            self.committee,
            None,
            None,
            None,
            None,
            None,
            schedule_data={
                "expenditure_date": "2024-01-10",
                "expenditure_amount": 40,
                "aggregate_general_elec_expended": 62
            }
        )
        transaction.aggregate = 62

        serializer = TransactionSerializer(
            context={"request": self.mock_request},
        )
        representation = serializer.to_representation(transaction)
        self.assertEqual(representation["aggregate"], '62.00')
        self.assertEqual(representation["aggregate_general_elec_expended"], '62.00')

    def test_to_representation_no_depth_skips_children_and_reports(self):
        report = create_form3x(self.committee, "2024-01-01", "2024-01-31", {})
        parent = create_schedule_a(
            "INDIVIDUAL_RECEIPT", self.committee, None, "2024-01-10", 100
        )
        child = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION", self.committee, None, "2024-01-11", 10
        )
        child.parent_transaction = parent
        child.save()
        parent.set_reports([report.id])

        serializer = TransactionSerializer(
            context={"request": self.mock_request, "no_depth": True},
        )
        representation = serializer.to_representation(parent)

        self.assertNotIn("children", representation)
        self.assertNotIn("report_ids", representation)
        self.assertEqual(len(representation["reports"]), 1)

    def test_schedule_c_serialization_includes_loan_agreement_id(self):
        report = create_form3x(self.committee, "2024-01-01", "2024-01-31", {})
        loan, _, loan_agreement, _ = create_loan_from_bank(
            self.committee,
            None,
            "5000.00",
            "2024-07-01",
            "7%",
            False,
            "2024-01-01",
            report=report,
        )

        serializer = TransactionSerializer(
            context={"request": self.mock_request},
        )
        representation = serializer.to_representation(loan)

        self.assertEqual(representation["loan_agreement_id"], loan_agreement.id)
