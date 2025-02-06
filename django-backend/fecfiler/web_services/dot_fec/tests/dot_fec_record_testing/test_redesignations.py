from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_transactions
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance, FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.tests.utils import create_schedule_b
from fecfiler.contacts.models import Contact
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class DotFECRedesignationsTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
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

        self.organization = Contact.objects.create(
            type=Contact.ContactType.ORGANIZATION,
            name="Test Org",
            committee_id=self.committee.id,
            street_1="5678 Road St",
            street_2="Apt 2",
            city="Denver",
            state="CO",
            zip="80014",
        )

        self.candidate = Contact.objects.create(
            type=Contact.ContactType.CANDIDATE,
            last_name="Candidate last",
            first_name="Candidate first",
            middle_name="Candidate middle",
            prefix="Mr.",
            suffix="Junior",
            committee_id=self.committee.committee_id,
            candidate_id="H8MA03131",
            candidate_office="H",
            candidate_state="AZ",
            candidate_district="01",
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

        self.disbursment = create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.individual,
            "2024-01-04",
            "250.00",
            "GENERAL_DISBURSEMENT",
            "SB21B",
            report=self.m1,
        )
        schedule_b = self.disbursment.schedule_b
        schedule_b.election_code = "H"
        schedule_b.election_other_description = "ELECTION DESCRIPTION"
        schedule_b.expenditure_purpose_descrip = "Exp Desc"
        schedule_b.category_code = "CODE"
        self.disbursment.contact_2 = self.candidate
        self.disbursment.contact_3 = self.organization
        schedule_b.conduit_name = "Conduit Name"
        schedule_b.conduit_street_1 = "Conduit St."
        schedule_b.conduit_street_2 = "Apt 1"
        schedule_b.conduit_city = "Conduit City"
        schedule_b.conduit_state = "AZ"
        schedule_b.conduit_zip = "10001"
        self.disbursment.memo_code = True
        schedule_b.memo_text_description = "MEMO DESC"
        schedule_b.reference_to_si_or_sl_system_code_that_identifies_the_account = (
            "Whatever this is"
        )
        schedule_b.save()
        self.disbursment.save()

        self.disbursment_copy = create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.individual,
            "2024-01-04",
            "250.00",
            "GENERAL_DISBURSEMENT",
            "SB21B",
            report=self.m2,
        )
        self.disbursment_copy.reatt_redes = self.disbursment
        self.disbursment_copy.schedule_b.expenditure_purpose_descrip = (
            "(Originally disclosed on January 20 MONTHLY REPORT (M1).) "
            "See redesignation below."
        )
        self.disbursment_copy.force_itemized = True
        self.disbursment_copy.schedule_b.reattribution_redesignation_tag = "REDESIGNATED"
        schedule_b = self.disbursment_copy.schedule_b
        schedule_b.election_code = "H"
        schedule_b.election_other_description = "ELECTION DESCRIPTION"
        schedule_b.expenditure_purpose_descrip = "Exp Desc"
        schedule_b.category_code = "CODE"
        self.disbursment.contact_2 = self.candidate
        self.disbursment.contact_3 = self.organization
        schedule_b.conduit_name = "Conduit Name"
        schedule_b.conduit_street_1 = "Conduit St."
        schedule_b.conduit_street_2 = "Apt 1"
        schedule_b.conduit_city = "Conduit City"
        schedule_b.conduit_state = "AZ"
        schedule_b.conduit_zip = "10001"
        self.disbursment.memo_code = True
        schedule_b.memo_text_description = "MEMO DESC"
        schedule_b.reference_to_si_or_sl_system_code_that_identifies_the_account = (
            "Whatever this is"
        )
        schedule_b.save()
        self.disbursment_copy.save()

        self.redesignation_to = create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.individual_2,
            "2024-01-01",
            "10.00",
            "GENERAL_DISBURSEMENT",
            "SB21B",
            report=self.m2,
        )

        self.redesignation_to.schedule_b.reattribution_redesignation_tag = (
            "REDESIGNATION_TO"
        )
        self.redesignation_to.schedule_b.expenditure_purpose_descrip = (
            f"Redesignation  to {self.individual_2.first_name} "
            f"{self.individual_2.last_name}"
        )
        self.redesignation_to.schedule_b.save()
        self.redesignation_to.force_itemized = True
        self.redesignation_to.reatt_redes = self.disbursment_copy
        self.redesignation_to.save()

        self.redesignation_from = create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.individual,
            "2024-01-01",
            "-10.00",
            "GENERAL_DISBURSEMENT",
            "SB21B",
            report=self.m2,
        )
        self.redesignation_from.force_itemized = True
        self.redesignation_from.schedule_b.reattribution_redesignation_tag = (
            "REDESIGNATION_FROM"
        )
        self.redesignation_from.schedule_b.expenditure_purpose_descrip = (
            f"Redesignation from {self.individual.first_name} {self.individual.last_name}"
        )
        self.redesignation_from.schedule_b.save()
        self.redesignation_from.reatt_redes = self.disbursment_copy
        self.redesignation_from.save()

        transactions = compose_transactions(self.m2.id)
        for transaction in transactions:
            logger.info(f"{transaction.transaction_id}: {transaction.amount}")
            if transaction.transaction_id == self.disbursment_copy.transaction_id:
                serialized_copy = serialize_instance("SchB", transaction)
            if transaction.transaction_id == self.redesignation_from.transaction_id:
                serialized_from = serialize_instance("SchB", transaction)
            if transaction.transaction_id == self.redesignation_to.transaction_id:
                serialized_to = serialize_instance("SchB", transaction)

        self.split_copy = serialized_copy.split(FS_STR)
        self.split_from = serialized_from.split(FS_STR)
        self.split_to = serialized_to.split(FS_STR)

    def test_form_type(self):
        self.assertEqual(self.disbursment_copy.form_type, "SB21B")
        for i in self.split_copy:
            logger.info(i)
        self.assertEqual(self.split_copy[0], "SB21B")
        self.assertEqual(self.split_from[0], "SB21B")
        self.assertEqual(self.split_to[0], "SB21B")

    def test_committee(self):
        self.assertEqual(self.split_copy[1], self.committee.committee_id)
        self.assertEqual(self.split_from[1], self.committee.committee_id)
        self.assertEqual(self.split_to[1], self.committee.committee_id)

    def test_transaction_id(self):
        self.assertEqual(self.split_copy[2], self.disbursment_copy.transaction_id)
        self.assertEqual(self.split_from[2], self.redesignation_from.transaction_id)
        self.assertEqual(self.split_to[2], self.redesignation_to.transaction_id)

    def test_back_reference(self):
        self.assertEqual(self.split_copy[3], self.disbursment.transaction_id)
        self.assertEqual(self.split_copy[4], self.disbursment.form_type)
        self.assertEqual(self.split_from[3], self.disbursment_copy.transaction_id)
        self.assertEqual(self.split_from[4], self.disbursment_copy.form_type)
        self.assertEqual(self.split_to[3], self.disbursment_copy.transaction_id)
        self.assertEqual(self.split_to[4], self.disbursment_copy.form_type)

    def test_payee(self):
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

    def test_purpose_descrip(self):
        self.assertEqual(
            self.split_copy[22],
            self.disbursment_copy.schedule_b.expenditure_purpose_descrip,
        )
        self.assertEqual(
            self.split_from[22],
            self.redesignation_from.schedule_b.expenditure_purpose_descrip,
        )
        self.assertEqual(
            self.split_to[22],
            self.redesignation_to.schedule_b.expenditure_purpose_descrip,
        )
