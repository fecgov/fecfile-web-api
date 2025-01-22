from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_transactions
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.tests.utils import create_schedule_b
from fecfiler.contacts.models import Contact
from datetime import datetime
from fecfiler.web_services.models import UploadSubmission
import structlog

logger = structlog.get_logger(__name__)


class DotFECScheduleBTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")

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

        coverage_from = datetime.strptime("2024-01-01", "%Y-%m-%d")
        coverage_through = datetime.strptime("2024-02-01", "%Y-%m-%d")
        self.f3x = create_form3x(
            self.committee,
            coverage_from,
            coverage_through,
            {},
        )

        upload_submission = UploadSubmission.objects.initiate_submission(self.f3x.id)
        self.f3x.upload_submission = upload_submission
        self.f3x.save()

        self.disbursment_individual = create_schedule_b(
            "OPERATING_EXPENDITURE",
            self.committee,
            self.individual,
            "2024-01-04",
            "250.00",
            "GENERAL_DISBURSEMENT",
            "SB21B",
            report=self.f3x,
        )
        schedule_b = self.disbursment_individual.schedule_b
        schedule_b.election_code = "H"
        schedule_b.election_other_description = "ELECTION DESCRIPTION"
        schedule_b.expenditure_purpose_descrip = "Exp Desc"
        schedule_b.category_code = "CODE"
        self.disbursment_individual.contact_2 = self.candidate
        self.disbursment_individual.contact_3 = self.organization
        schedule_b.conduit_name = "Conduit Name"
        schedule_b.conduit_street_1 = "Conduit St."
        schedule_b.conduit_street_2 = "Apt 1"
        schedule_b.conduit_city = "Conduit City"
        schedule_b.conduit_state = "AZ"
        schedule_b.conduit_zip = "10001"
        self.disbursment_individual.memo_code = True
        schedule_b.memo_text_description = "MEMO DESC"
        schedule_b.reference_to_si_or_sl_system_code_that_identifies_the_account = (
            "Whatever this is"
        )
        schedule_b.save()
        self.disbursment_individual.save()

        self.disbursment_organization = create_schedule_b(
            "TRANSFER_TO_AFFILIATES",
            self.committee,
            self.organization,
            "2024-01-10",
            "450.00",
            "GENERAL_DISBURSEMENT",
            "SB21B",
            report=self.f3x,
        )

        self.disbursment_organization.schedule_b.expenditure_purpose_descrip = (
            "Exp Purpose Desc"
        )
        self.disbursment_organization.contact_2 = self.candidate
        self.disbursment_organization.schedule_b.save()
        self.disbursment_organization.save()

        transactions = compose_transactions(self.f3x.id)
        serialized_transaction = serialize_instance("SchB", transactions[0])
        self.split_row = serialized_transaction.split(FS_STR)
        serialized_transaction_org = serialize_instance("SchB", transactions[1])
        self.split_row_org = serialized_transaction_org.split(FS_STR)

    def test_form_type(self):
        self.assertEqual(self.split_row[0], "SB21B")

    def test_committee(self):
        self.assertEqual(self.split_row[1], self.committee.committee_id)

    def test_transaction_id(self):
        self.assertEqual(self.split_row[2], self.disbursment_individual.transaction_id)
        self.assertEqual(
            self.split_row_org[2], self.disbursment_organization.transaction_id
        )

    def test_entity_type(self):
        self.assertEqual(self.split_row[5], "IND")
        self.assertEqual(self.split_row_org[5], "ORG")

    def test_payee_individual(self):
        self.assertEqual(self.split_row[6], "")
        self.assertEqual(self.split_row[7], self.individual.last_name)
        self.assertEqual(self.split_row[8], self.individual.first_name)
        self.assertEqual(self.split_row[9], self.individual.middle_name)
        self.assertEqual(self.split_row[10], self.individual.prefix)
        self.assertEqual(self.split_row[11], self.individual.suffix)
        self.assertEqual(self.split_row[12], self.individual.street_1)
        self.assertEqual(self.split_row[13], self.individual.street_2)
        self.assertEqual(self.split_row[14], self.individual.city)
        self.assertEqual(self.split_row[15], self.individual.state)
        self.assertEqual(self.split_row[16], self.individual.zip)

    def test_payee_organization(self):
        self.assertEqual(self.split_row_org[6], self.organization.name)
        self.assertEqual(self.split_row_org[7], "")
        self.assertEqual(self.split_row_org[8], "")
        self.assertEqual(self.split_row_org[9], "")
        self.assertEqual(self.split_row_org[10], "")
        self.assertEqual(self.split_row_org[11], "")
        self.assertEqual(self.split_row_org[12], self.organization.street_1)
        self.assertEqual(self.split_row_org[13], self.organization.street_2)
        self.assertEqual(self.split_row_org[14], self.organization.city)
        self.assertEqual(self.split_row_org[15], self.organization.state)
        self.assertEqual(self.split_row_org[16], self.organization.zip)

    def test_election(self):
        self.assertEqual(self.split_row[17], "H")
        self.assertEqual(self.split_row[18], "ELECTION DESCRIPTION")

    def test_expenditure_individual(self):
        self.assertEqual(self.split_row[19], "20240104")
        self.assertEqual(self.split_row[20], "250.00")
        self.assertEqual(self.split_row[21], "")
        self.assertEqual(self.split_row[22], "Exp Desc")

    def test_expenditure_organization(self):
        self.assertEqual(self.split_row_org[19], "20240110")
        self.assertEqual(self.split_row_org[20], "450.00")
        self.assertEqual(self.split_row_org[21], "")
        self.assertEqual(self.split_row_org[22], "Exp Purpose Desc")

    def test_category_code(self):
        self.assertEqual(self.split_row[23], "CODE")

    def test_beneficiary(self):
        self.assertEqual(self.split_row[24], str(self.committee.id))
        self.assertEqual(self.split_row[25], self.organization.name)
        self.assertEqual(self.split_row[26], self.candidate.candidate_id)
        self.assertEqual(self.split_row[27], self.candidate.last_name)
        self.assertEqual(self.split_row[28], self.candidate.first_name)
        self.assertEqual(self.split_row[29], self.candidate.middle_name)
        self.assertEqual(self.split_row[30], self.candidate.prefix)
        self.assertEqual(self.split_row[31], self.candidate.suffix)
        self.assertEqual(self.split_row[32], self.candidate.candidate_office)
        self.assertEqual(self.split_row[33], self.candidate.candidate_state)
        self.assertEqual(self.split_row[34], self.candidate.candidate_district)

    def test_conduit(self):
        self.assertEqual(self.split_row[35], "Conduit Name")
        self.assertEqual(self.split_row[36], "Conduit St.")
        self.assertEqual(self.split_row[37], "Apt 1")
        self.assertEqual(self.split_row[38], "Conduit City")
        self.assertEqual(self.split_row[39], "AZ")
        self.assertEqual(self.split_row[40], "10001")

    def test_memo(self):
        self.assertEqual(self.split_row[41], "X")
        self.assertEqual(self.split_row[42], "MEMO DESC")

    def test_reference_to_si_or_sl_system_code_that_identifies_the_account(self):
        self.assertEqual(self.split_row[43], "Whatever this is")
