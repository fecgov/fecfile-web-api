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
import structlog

logger = structlog.get_logger(__name__)


class DotFECScheduleC1TestCase(TestCase):
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

        loan, loan_receipt, self.loan_agreement, guarantor = create_loan_from_bank(
            self.committee,
            self.organization,
            Decimal(5000.00),
            datetime.strptime("2024-01-10", "%Y-%m-%d"),
            "7%",
            loan_incurred_date=datetime.strptime("2024-01-02", "%Y-%m-%d"),
            report=self.f3x,
        )

        self.loan_agreement.entity_type = "IND"
        self.loan_agreement.schedule_c1.loan_restructured = True
        self.loan_agreement.schedule_c1.loan_originally_incurred_date = datetime.strptime(
            "2024-01-12", "%Y-%m-%d"
        )
        self.loan_agreement.schedule_c1.credit_amount_this_draw = "25.00"
        self.loan_agreement.schedule_c1.total_balance = Decimal(5025.00)
        self.loan_agreement.schedule_c1.others_liable = True
        self.loan_agreement.schedule_c1.collateral = True
        self.loan_agreement.schedule_c1.desc_collateral = "DESC COLLATERAL"
        self.loan_agreement.schedule_c1.collateral_value_amount = Decimal(100.00)
        self.loan_agreement.schedule_c1.perfected_interest = True
        self.loan_agreement.schedule_c1.future_income = True
        self.loan_agreement.schedule_c1.desc_specification_of_the_above = "SPEC ABOVE"
        self.loan_agreement.schedule_c1.estimated_value = Decimal(125.00)
        self.loan_agreement.schedule_c1.depository_account_established_date = (
            datetime.strptime("2023-01-12", "%Y-%m-%d")
        )
        self.loan_agreement.schedule_c1.ind_name_account_location = "HOME"
        self.loan_agreement.schedule_c1.account_street_1 = "HOME ADDRESS"
        self.loan_agreement.schedule_c1.account_street_2 = "101 Home Street"
        self.loan_agreement.schedule_c1.account_city = "Home City"
        self.loan_agreement.schedule_c1.account_state = "AZ"
        self.loan_agreement.schedule_c1.account_zip = "10001"
        self.loan_agreement.schedule_c1.dep_acct_auth_date_presidential = (
            datetime.strptime("2023-01-14", "%Y-%m-%d")
        )
        self.loan_agreement.schedule_c1.basis_of_loan_description = "BASIS"
        self.loan_agreement.schedule_c1.treasurer_last_name = "McTester"
        self.loan_agreement.schedule_c1.treasurer_first_name = "Test"
        self.loan_agreement.schedule_c1.treasurer_middle_name = "Testerson"
        self.loan_agreement.schedule_c1.treasurer_prefix = "Mr."
        self.loan_agreement.schedule_c1.treasurer_suffix = "Junior"
        self.loan_agreement.schedule_c1.treasurer_date_signed = datetime.strptime(
            "2024-01-14", "%Y-%m-%d"
        )
        self.loan_agreement.schedule_c1.authorized_last_name = "Last Name"
        self.loan_agreement.schedule_c1.authorized_first_name = "First Name"
        self.loan_agreement.schedule_c1.authorized_middle_name = "Middle Name"
        self.loan_agreement.schedule_c1.authorized_prefix = "Prefix"
        self.loan_agreement.schedule_c1.authorized_suffix = "Suffix"
        self.loan_agreement.schedule_c1.authorized_title = "McTitle"
        self.loan_agreement.schedule_c1.authorized_date_signed = datetime.strptime(
            "2024-01-15", "%Y-%m-%d"
        )
        self.loan_agreement.schedule_c1.save()
        self.loan_agreement.save()

        self.transactions = compose_transactions(self.f3x.id)
        serialized_transaction = serialize_instance("SchC1", self.transactions[3])
        self.split_row = serialized_transaction.split(FS_STR)

    def test_form_type(self):
        for i in self.split_row:
            logger.info(i)
        self.assertEqual(self.split_row[0], "SC1/10")

    def test_committee(self):
        self.assertEqual(self.split_row[1], self.committee.committee_id)

    def test_transaction_id(self):
        self.assertEqual(self.split_row[2], self.loan_agreement.transaction_id)

    def test_lender_organization(self):
        self.assertEqual(self.split_row[4], self.organization.name)
        self.assertEqual(self.split_row[5], self.organization.street_1)
        self.assertEqual(self.split_row[6], self.organization.street_2)
        self.assertEqual(self.split_row[7], self.organization.city)
        self.assertEqual(self.split_row[8], self.organization.state)
        self.assertEqual(self.split_row[9], self.organization.zip)

    def test_loan_agreement(self):
        self.assertEqual(self.split_row[10], "5000.00")
        self.assertEqual(self.split_row[11], "7%")
        self.assertEqual(self.split_row[12], "20240102")
        self.assertEqual(self.split_row[13], "20240110")
        self.assertEqual(self.split_row[14], "Y")
        self.assertEqual(self.split_row[15], "20240112")
        self.assertEqual(self.split_row[16], "25.00")
        self.assertEqual(self.split_row[17], "5025.00")
        self.assertEqual(self.split_row[18], "Y")
        self.assertEqual(self.split_row[19], "Y")
        self.assertEqual(self.split_row[20], "DESC COLLATERAL")
        self.assertEqual(self.split_row[21], "100.00")
        self.assertEqual(self.split_row[22], "Y")
        self.assertEqual(self.split_row[23], "Y")
        self.assertEqual(self.split_row[24], "SPEC ABOVE")
        self.assertEqual(self.split_row[25], "125.00")

    def test_account(self):
        self.assertEqual(self.split_row[26], "20230112")
        self.assertEqual(self.split_row[27], "HOME")
        self.assertEqual(self.split_row[28], "HOME ADDRESS")
        self.assertEqual(self.split_row[29], "101 Home Street")
        self.assertEqual(self.split_row[30], "Home City")
        self.assertEqual(self.split_row[31], "AZ")
        self.assertEqual(self.split_row[32], "10001")
        self.assertEqual(self.split_row[33], "20230114")

    def test_basis_of_loan_description(self):
        self.assertEqual(self.split_row[34], "BASIS")

    def test_treasurer(self):
        self.assertEqual(self.split_row[35], "McTester")
        self.assertEqual(self.split_row[36], "Test")
        self.assertEqual(self.split_row[37], "Testerson")
        self.assertEqual(self.split_row[38], "Mr.")
        self.assertEqual(self.split_row[39], "Junior")
        self.assertEqual(self.split_row[40], "20240114")

    def test_authorized(self):
        self.assertEqual(self.split_row[41], "Last Name")
        self.assertEqual(self.split_row[42], "First Name")
        self.assertEqual(self.split_row[43], "Middle Name")
        self.assertEqual(self.split_row[44], "Prefix")
        self.assertEqual(self.split_row[45], "Suffix")
        self.assertEqual(self.split_row[46], "McTitle")
        self.assertEqual(self.split_row[47], "20240115")
