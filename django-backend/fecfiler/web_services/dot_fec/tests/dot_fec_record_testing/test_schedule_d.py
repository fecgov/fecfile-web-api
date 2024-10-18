from decimal import Decimal
from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_transactions
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.tests.utils import create_debt
from fecfiler.contacts.models import Contact
from datetime import datetime
from fecfiler.web_services.models import UploadSubmission
import structlog

logger = structlog.get_logger(__name__)


class DotFECScheduleDTestCase(TestCase):
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
            committee_account_id=self.committee.id,
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
            committee_account_id=self.committee.id,
            street_1="5678 Road St",
            street_2="Apt 2",
            city="Denver",
            state="CO",
            zip="80014",
        )

        self.debt_individual = create_debt(
            self.committee, self.individual, Decimal("123.00"), report=self.f3x
        )

        self.debt_individual.entity_type = "IND"
        self.debt_individual.schedule_d.purpose_of_debt_or_obligation = "TEST DEBT"
        self.debt_individual.schedule_d.save()
        self.debt_individual.save()

        self.debt_organization = create_debt(
            self.committee, self.organization, Decimal("456.00"), report=self.f3x
        )

        self.debt_organization.entity_type = "ORG"
        self.debt_organization.save()

        transactions = compose_transactions(self.f3x.id)
        serialized_transaction = serialize_instance("SchD", transactions[0])
        self.split_row = serialized_transaction.split(FS_STR)
        serialized_transaction_org = serialize_instance("SchD", transactions[1])
        self.split_row_org = serialized_transaction_org.split(FS_STR)

    def test_form_type(self):
        self.assertEqual(self.split_row[0], "SD9")

    def test_committee(self):
        self.assertEqual(self.split_row[1], self.committee.committee_id)

    def test_transaction_id(self):
        self.assertEqual(self.split_row[2], self.debt_individual.transaction_id)

    def test_entity_type(self):
        self.assertEqual(self.split_row[3], "IND")
        self.assertEqual(self.split_row_org[3], "ORG")

    def test_creditor_individual(self):
        self.assertEqual(self.split_row[4], "")
        self.assertEqual(self.split_row[5], self.individual.last_name)
        self.assertEqual(self.split_row[6], self.individual.first_name)
        self.assertEqual(self.split_row[7], self.individual.middle_name)
        self.assertEqual(self.split_row[8], self.individual.prefix)
        self.assertEqual(self.split_row[9], self.individual.suffix)
        self.assertEqual(self.split_row[10], self.individual.street_1)
        self.assertEqual(self.split_row[11], self.individual.street_2)
        self.assertEqual(self.split_row[12], self.individual.city)
        self.assertEqual(self.split_row[13], self.individual.state)
        self.assertEqual(self.split_row[14], self.individual.zip)

    def test_creditor_organization(self):
        self.assertEqual(self.split_row_org[4], self.organization.name)
        self.assertEqual(self.split_row_org[5], "")
        self.assertEqual(self.split_row_org[6], "")
        self.assertEqual(self.split_row_org[7], "")
        self.assertEqual(self.split_row_org[8], "")
        self.assertEqual(self.split_row_org[9], "")
        self.assertEqual(self.split_row_org[10], self.organization.street_1)
        self.assertEqual(self.split_row_org[11], self.organization.street_2)
        self.assertEqual(self.split_row_org[12], self.organization.city)
        self.assertEqual(self.split_row_org[13], self.organization.state)
        self.assertEqual(self.split_row_org[14], self.organization.zip)

    def test_purpose_of_debt(self):
        self.assertEqual(self.split_row[15], "TEST DEBT")

    def test_balance(self):
        self.assertEqual(self.split_row[16], "0")
        self.assertEqual(self.split_row[17], "123.00")
        self.assertEqual(self.split_row[18], "0")
        self.assertEqual(self.split_row[19], "123.00")
