from decimal import Decimal
from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_transactions
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.tests.utils import create_loan_from_bank
from fecfiler.contacts.models import Contact
from datetime import datetime
from fecfiler.web_services.models import UploadSubmission
from unittest.mock import patch
import structlog

logger = structlog.get_logger(__name__)


class DotFECScheduleC2TestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
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

        self.individual = Contact.objects.create(
            type=Contact.ContactType.INDIVIDUAL,
            last_name="last name",
            first_name="First name",
            committee_id="C87654321",
            middle_name="Middle Name",
            prefix="Mr.",
            suffix="Junior",
            street_1="1234 Street Rd",
            street_2="Apt 1",
            city="Phoenix",
            state="AZ",
            zip="85018",
            employer="Test Employer",
            occupation="Tester",
        )

        loan, loan_receipt, loan_agreement, self.guarantor = create_loan_from_bank(
            self.committee,
            self.organization,
            Decimal(5000.00),
            datetime.strptime("2024-01-10", "%Y-%m-%d"),
            "7%",
            loan_incurred_date=datetime.strptime("2024-01-02", "%Y-%m-%d"),
            report=self.f3x,
        )

        self.guarantor.contact_1 = self.individual
        self.guarantor.schedule_c2.guaranteed_amount = Decimal(10.00)
        self.guarantor.schedule_c2.save()
        self.guarantor.save()

        self.transactions = compose_transactions(self.f3x.id)
        serialized_transaction = serialize_instance("SchC2", self.transactions[2])
        self.split_row = serialized_transaction.split(FS_STR)

    def test_form_type(self):
        self.assertEqual(self.split_row[0], "SC2/10")

    def test_committee(self):
        self.assertEqual(self.split_row[1], self.committee.committee_id)

    def test_transaction_id(self):
        self.assertEqual(self.split_row[2], self.guarantor.transaction_id)

    def test_guarantor(self):
        self.assertEqual(self.split_row[4], self.individual.type)
        self.assertEqual(self.split_row[5], "")
        self.assertEqual(self.split_row[6], self.individual.committee_id)
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
        self.assertEqual(self.split_row[17], self.individual.employer)
        self.assertEqual(self.split_row[18], self.individual.occupation)
        self.assertEqual(self.split_row[19], "10.00")
