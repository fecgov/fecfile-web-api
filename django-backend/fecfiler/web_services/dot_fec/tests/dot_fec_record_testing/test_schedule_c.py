from decimal import Decimal
from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_transactions
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.tests.utils import create_loan
from fecfiler.contacts.models import Contact
from datetime import datetime
from fecfiler.web_services.models import UploadSubmission
import structlog

logger = structlog.get_logger(__name__)


class DotFECScheduleCTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
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

        self.loan_individual = create_loan(
            self.committee,
            self.individual,
            Decimal(5000.00),
            datetime.strptime("2024-01-10", "%Y-%m-%d"),
            "7%",
            loan_incurred_date=datetime.strptime("2024-01-02", "%Y-%m-%d"),
            report=self.f3x,
        )

        self.loan_individual.contact_2 = self.candidate
        self.loan_individual.entity_type = "IND"
        self.loan_individual.memo_code = True
        self.loan_individual.schedule_c.memo_text_description = "MEMO TEXT"
        self.loan_individual.schedule_c.election_code = "H"
        self.loan_individual.schedule_c.election_other_description = (
            "ELECTION DESCRIPTION"
        )
        self.loan_individual.schedule_c.save()
        self.loan_individual.save()

        self.loan_organization = create_loan(
            self.committee,
            self.organization,
            "3000.00",
            "2024-01-03",
            "8%",
            loan_incurred_date=datetime.strptime("2024-01-04", "%Y-%m-%d"),
            report=self.f3x,
        )

        self.loan_organization.contact_2 = self.candidate
        self.loan_organization.entity_type = "ORG"
        self.loan_organization.schedule_c.secured = True
        self.loan_organization.schedule_c.personal_funds = True
        self.loan_organization.schedule_c.save()
        self.loan_organization.save()

        transactions = compose_transactions(self.f3x.id)
        serialized_transaction = serialize_instance("SchC", transactions[0])
        self.split_row = serialized_transaction.split(FS_STR)
        serialized_transaction_org = serialize_instance("SchC", transactions[1])
        self.split_row_org = serialized_transaction_org.split(FS_STR)

    def test_form_type(self):
        for i in self.split_row_org:
            logger.info(i)
        self.assertEqual(self.split_row[0], "SC/9")

    def test_committee(self):
        self.assertEqual(self.split_row[1], self.committee.committee_id)

    def test_transaction_id(self):
        self.assertEqual(self.split_row[2], self.loan_individual.transaction_id)

    def test_receipt_line_number(self):
        self.assertEqual(self.split_row[3], "")

    def test_entity_type(self):
        self.assertEqual(self.split_row[4], "IND")
        self.assertEqual(self.split_row_org[4], "ORG")

    def test_lender_individual(self):
        self.assertEqual(self.split_row[5], "")
        self.assertEqual(self.split_row[6], self.individual.last_name)
        self.assertEqual(self.split_row[7], self.individual.first_name)
        self.assertEqual(self.split_row[8], self.individual.middle_name)
        self.assertEqual(self.split_row[9], self.individual.prefix)
        self.assertEqual(self.split_row[10], self.individual.suffix)
        self.assertEqual(self.split_row[11], self.individual.street_1)
        self.assertEqual(self.split_row[12], self.individual.street_2)
        self.assertEqual(self.split_row[13], self.individual.city)
        self.assertEqual(self.split_row[14], self.individual.state)
        self.assertEqual(self.split_row[15], self.individual.zip)

    def test_lender_organization(self):
        self.assertEqual(self.split_row_org[5], self.organization.name)
        self.assertEqual(self.split_row_org[6], "")
        self.assertEqual(self.split_row_org[7], "")
        self.assertEqual(self.split_row_org[8], "")
        self.assertEqual(self.split_row_org[9], "")
        self.assertEqual(self.split_row_org[10], "")
        self.assertEqual(self.split_row_org[11], self.organization.street_1)
        self.assertEqual(self.split_row_org[12], self.organization.street_2)
        self.assertEqual(self.split_row_org[13], self.organization.city)
        self.assertEqual(self.split_row_org[14], self.organization.state)
        self.assertEqual(self.split_row_org[15], self.organization.zip)

    def test_election(self):
        self.assertEqual(self.split_row[16], "H")
        self.assertEqual(self.split_row[17], "ELECTION DESCRIPTION")

    def test_loan_individual(self):
        self.assertEqual(self.split_row[18], "5000.00")
        self.assertEqual(self.split_row[19], "0.00")
        self.assertEqual(self.split_row[20], "5000.00")
        self.assertEqual(self.split_row[21], "20240102")
        self.assertEqual(self.split_row[22], "20240110")
        self.assertEqual(self.split_row[23], "7%")
        self.assertEqual(self.split_row[24], "N")
        self.assertEqual(self.split_row[25], "N")
        self.assertEqual(self.split_row[26], "C00000000")

    def test_loan_organization(self):
        self.assertEqual(self.split_row_org[18], "3000.00")
        self.assertEqual(self.split_row_org[19], "0.00")
        self.assertEqual(self.split_row_org[20], "3000.00")
        self.assertEqual(self.split_row_org[21], "20240104")
        self.assertEqual(self.split_row_org[22], "20240103")
        self.assertEqual(self.split_row_org[23], "8%")
        self.assertEqual(self.split_row_org[24], "Y")
        self.assertEqual(self.split_row_org[25], "Y")
        self.assertEqual(self.split_row[26], "C00000000")

    def test_lender(self):
        self.assertEqual(self.split_row[27], self.candidate.candidate_id)
        self.assertEqual(self.split_row[28], self.candidate.last_name)
        self.assertEqual(self.split_row[29], self.candidate.first_name)
        self.assertEqual(self.split_row[30], self.candidate.middle_name)
        self.assertEqual(self.split_row[31], self.candidate.prefix)
        self.assertEqual(self.split_row[32], self.candidate.suffix)
        self.assertEqual(self.split_row[33], self.candidate.candidate_office)
        self.assertEqual(self.split_row[34], self.candidate.candidate_state)
        self.assertEqual(self.split_row[35], self.candidate.candidate_district)

    def test_memo(self):
        self.assertEqual(self.split_row[36], "X")
        self.assertEqual(self.split_row[37], "MEMO TEXT")
