from django.test import TestCase
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_transactions
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance, FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.tests.utils import create_schedule_a
from fecfiler.contacts.models import Contact
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class DotFECReattributionsTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
        coverage_from = datetime.strptime("2024-01-01", "%Y-%m-%d")
        coverage_through = datetime.strptime("2024-01-31", "%Y-%m-%d")
        self.m1 = create_form3x(
            self.committee,
            coverage_from,
            coverage_through,
            {"L38_net_operating_expenditures_ytd": format(381.00, ".2f")},
            report_code="M1",
        )

        coverage_from = datetime.strptime("2024-02-01", "%Y-%m-%d")
        coverage_through = datetime.strptime("2024-02-27", "%Y-%m-%d")
        self.m2 = create_form3x(
            self.committee,
            coverage_from,
            coverage_through,
            {"L38_net_operating_expenditures_ytd": format(381.00, ".2f")},
            report_code="M2",
        )

        self.individual = Contact.objects.create(
            type=Contact.ContactType.INDIVIDUAL,
            last_name="last name",
            first_name="First name",
            committee_id=self.committee.committee_id,
            middle_name="Middle Name",
            prefix="Mr.",
            suffix="Junior",
            street_1="1234 Street Rd",
            street_2="Apt 1",
            city="Phoenix",
            state="AZ",
            zip="85018",
        )

        self.individual_2 = Contact.objects.create(
            type=Contact.ContactType.INDIVIDUAL,
            last_name="last name 2",
            first_name="First name 2",
            committee_id=self.committee.committee_id,
            middle_name="Middle Name 2",
            prefix="Mr. 2",
            suffix="Junior 2",
            street_1="4321 Street Rd",
            street_2="Apt 2",
            city="Denver",
            state="CO",
            zip="10001",
        )

        self.individual_receipt = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.individual,
            datetime.strptime("2024-01-09", "%Y-%m-%d"),
            "15.00",
            "GENERAL",
            "SA11AI",
            purpose_description="Testing Aggregate Transaction",
            report=self.m1,
        )

        self.receipt_copy = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.individual,
            "2024-01-01",
            amount="100.00",
            report=self.m2,
            itemized=True,
        )
        self.receipt_copy.reatt_redes = self.individual_receipt
        self.receipt_copy.schedule_a.contribution_purpose_descrip = (
            "(Originally disclosed on January 20 MONTHLY REPORT (M1).) "
            "See reattribution below."
        )
        self.receipt_copy.schedule_a.reattribution_redesignation_tag = "REATTRIBUTED"
        self.receipt_copy.schedule_a.save()
        self.receipt_copy.save()
        self.reattribution_to = create_schedule_a(
            "PARTNERSHIP_RECEIPT",
            self.committee,
            self.individual_2,
            "2024-01-01",
            amount="10.00",
            report=self.m2,
            itemized=True,
        )
        self.reattribution_to.schedule_a.reattribution_redesignation_tag = (
            "REATTRIBUTED_TO"
        )
        self.reattribution_to.schedule_a.contribution_purpose_descrip = (
            f"Reattribution to {self.individual_2.first_name} "
            f"{self.individual_2.last_name}"
        )
        self.reattribution_to.schedule_a.save()
        self.reattribution_to.reatt_redes = self.receipt_copy
        self.reattribution_to.save()
        self.reattribution_from = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.individual,
            "2024-01-01",
            amount="-10.00",
            parent_id=self.reattribution_to.id,
            report=self.m2,
            itemized=True,
        )
        self.reattribution_from.schedule_a.reattribution_redesignation_tag = (
            "REATTRIBUTED_FROM"
        )
        self.reattribution_from.schedule_a.contribution_purpose_descrip = (
            f"Reattribution from {self.individual.first_name} {self.individual.last_name}"
        )
        self.reattribution_from.schedule_a.save()
        self.reattribution_from.reatt_redes = self.receipt_copy
        self.reattribution_from.save()

        transactions = compose_transactions(self.m2.id)
        for transaction in transactions:
            if transaction.transaction_id == self.receipt_copy.transaction_id:
                serialized_copy = serialize_instance("SchA", transaction)
            if transaction.transaction_id == self.reattribution_from.transaction_id:
                serialized_from = serialize_instance("SchA", transaction)
            if transaction.transaction_id == self.reattribution_to.transaction_id:
                serialized_to = serialize_instance("SchA", transaction)

        self.split_copy = serialized_copy.split(FS_STR)
        self.split_from = serialized_from.split(FS_STR)
        self.split_to = serialized_to.split(FS_STR)

    def test_form_type(self):
        self.assertEqual(self.receipt_copy.form_type, "SA11I")
        for i in self.split_copy:
            logger.info(i)
        self.assertEqual(self.split_copy[0], "SA11I")
        self.assertEqual(self.split_from[0], "SA11I")
        self.assertEqual(self.split_to[0], "SA11I")

    def test_committee(self):
        self.assertEqual(self.split_copy[1], self.committee.committee_id)
        self.assertEqual(self.split_from[1], self.committee.committee_id)
        self.assertEqual(self.split_to[1], self.committee.committee_id)

    def test_transaction_id(self):
        self.assertEqual(self.split_copy[2], self.receipt_copy.transaction_id)
        self.assertEqual(self.split_from[2], self.reattribution_from.transaction_id)
        self.assertEqual(self.split_to[2], self.reattribution_to.transaction_id)

    def test_back_reference(self):
        self.assertEqual(self.split_copy[3], self.individual_receipt.transaction_id)
        self.assertEqual(self.split_copy[4], self.individual_receipt.form_type)
        self.assertEqual(self.split_from[3], self.receipt_copy.transaction_id)
        self.assertEqual(self.split_from[4], self.receipt_copy.form_type)
        self.assertEqual(self.split_to[3], self.receipt_copy.transaction_id)
        self.assertEqual(self.split_to[4], self.receipt_copy.form_type)

    def test_contributor(self):
        self.assertEqual(self.split_copy[6], "")
        self.assertEqual(self.split_copy[7], self.individual.last_name)
        self.assertEqual(self.split_copy[8], self.individual.first_name)
        self.assertEqual(self.split_copy[9], self.individual.middle_name)
        self.assertEqual(self.split_copy[10], self.individual.prefix)
        self.assertEqual(self.split_copy[11], self.individual.suffix)
        self.assertEqual(self.split_copy[12], self.individual.street_1)
        self.assertEqual(self.split_copy[13], self.individual.street_2)
        self.assertEqual(self.split_copy[14], self.individual.city)
        self.assertEqual(self.split_copy[15], self.individual.state)
        self.assertEqual(self.split_copy[16], self.individual.zip)

        self.assertEqual(self.split_to[6], "")
        self.assertEqual(self.split_to[7], self.individual_2.last_name)
        self.assertEqual(self.split_to[8], self.individual_2.first_name)
        self.assertEqual(self.split_to[9], self.individual_2.middle_name)
        self.assertEqual(self.split_to[10], self.individual_2.prefix)
        self.assertEqual(self.split_to[11], self.individual_2.suffix)
        self.assertEqual(self.split_to[12], self.individual_2.street_1)
        self.assertEqual(self.split_to[13], self.individual_2.street_2)
        self.assertEqual(self.split_to[14], self.individual_2.city)
        self.assertEqual(self.split_to[15], self.individual_2.state)
        self.assertEqual(self.split_to[16], self.individual_2.zip)

        self.assertEqual(self.split_from[6], "")
        self.assertEqual(self.split_from[7], self.individual.last_name)
        self.assertEqual(self.split_from[8], self.individual.first_name)
        self.assertEqual(self.split_from[9], self.individual.middle_name)
        self.assertEqual(self.split_from[10], self.individual.prefix)
        self.assertEqual(self.split_from[11], self.individual.suffix)
        self.assertEqual(self.split_from[12], self.individual.street_1)
        self.assertEqual(self.split_from[13], self.individual.street_2)
        self.assertEqual(self.split_from[14], self.individual.city)
        self.assertEqual(self.split_from[15], self.individual.state)
        self.assertEqual(self.split_from[16], self.individual.zip)

    def test_contribution_purpose_descrip(self):
        self.assertEqual(
            self.split_copy[22], self.receipt_copy.schedule_a.contribution_purpose_descrip
        )
        self.assertEqual(
            self.split_from[22],
            self.reattribution_from.schedule_a.contribution_purpose_descrip,
        )
        self.assertEqual(
            self.split_to[22],
            self.reattribution_to.schedule_a.contribution_purpose_descrip,
        )
