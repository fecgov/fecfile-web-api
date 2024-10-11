from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_transactions
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.tests.utils import create_ie, create_schedule_a
from fecfiler.contacts.models import Contact
from datetime import datetime
from fecfiler.web_services.models import UploadSubmission
from fecfiler.transactions.serializers import REATTRIBUTED
import structlog

logger = structlog.get_logger(__name__)


class DotFECScheduleETestCase(TestCase):
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

        self.contact_1 = Contact.objects.create(
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

        self.contact_2 = Contact.objects.create(
            type=Contact.ContactType.CANDIDATE,
            last_name="last name",
            first_name="First name",
            committee_account_id=self.committee.id,
            candidate_id="H8MA03131",
            candidate_office="S",
            candidate_state="AK",
            candidate_district="01",
            middle_name="Middle Name",
            prefix="Mr.",
            suffix="Junior",
        )

        self.contact_3 = Contact.objects.create(
            type=Contact.ContactType.ORGANIZATION,
            name="Test Org",
            committee_account_id=self.committee.id,
            street_1="5678 Road St",
            street_2="Apt 2",
            city="Denver",
            state="CO",
            zip="80014",
        )

        self.transaction = create_schedule_a(
            "INDIVIDUAL_RECEIPT", self.committee, None, None, 1
        )
        self.transaction.schedule_a.reattribution_redesignation_tag = REATTRIBUTED
        self.transaction.schedule_a.save()
        self.transaction.save()

        self.ie = create_ie(
            self.committee,
            self.contact_1,
            datetime.strptime("2024-01-12", "%Y-%m-%d"),
            datetime.strptime("2024-01-15", "%Y-%m-%d"),
            "153.00",
            "C2012",
            self.contact_2,
            report=self.f3x,
        )
        self.ie.entity_type = "IND"
        self.ie.schedule_e.election_other_description = "OTHER DESCRIPTION"
        self.ie.schedule_e.expenditure_purpose_descrip = "EXPENDITURE DESCRIPTION"
        self.ie.schedule_e.category_code = "CODE"
        self.ie.schedule_e.payee_cmtte_fec_id_number = "TEST_ID"
        self.ie.schedule_e.support_oppose_code = "S"
        self.ie.schedule_e.memo_text_description = "MEMO TEXT DESCRIPTION"
        self.ie.memo_code = True
        self.ie.schedule_e.date_signed = datetime.today()
        self.ie.force_itemized = True
        self.ie.reatt_redes = self.transaction

        # Completing
        self.ie.schedule_e.completing_last_name = "LAST NAME"
        self.ie.schedule_e.completing_first_name = "FIRST NAME"
        self.ie.schedule_e.completing_middle_name = "MIDDLE NAME"
        self.ie.schedule_e.completing_prefix = "Mr."
        self.ie.schedule_e.completing_suffix = "Junior"

        self.ie.schedule_e.save()
        self.ie.save()

        self.ie_org = create_ie(
            self.committee,
            self.contact_3,
            datetime.strptime("2024-01-12", "%Y-%m-%d"),
            datetime.strptime("2024-01-15", "%Y-%m-%d"),
            "153.00",
            "C2012",
            self.contact_2,
            report=self.f3x,
        )

        transactions = compose_transactions(self.f3x.id)
        serialized_transaction = serialize_instance("SchE", transactions[0])
        serialized_transaction_org = serialize_instance("SchE", transactions[1])
        self.split_row = serialized_transaction.split(FS_STR)
        self.split_row_org = serialized_transaction_org.split(FS_STR)

    def test_form_type(self):
        self.assertEqual(self.split_row[0], "SE")

    def test_committee(self):
        self.assertEqual(self.split_row[1], self.committee.committee_id)

    def test_transaction_id(self):
        self.assertEqual(self.split_row[2], self.ie.transaction_id)

    def test_back_reference(self):
        self.assertEqual(self.split_row[3], self.transaction.transaction_id)
        self.assertEqual(self.split_row[4], "SA11I")

    def test_entity_type(self):
        self.assertEqual(self.split_row[5], "IND")

    def test_payee(self):
        self.assertEqual(self.split_row[6], "")
        self.assertEqual(self.split_row[7], self.contact_1.last_name)
        self.assertEqual(self.split_row[8], self.contact_1.first_name)
        self.assertEqual(self.split_row[9], self.contact_1.middle_name)
        self.assertEqual(self.split_row[10], self.contact_1.prefix)
        self.assertEqual(self.split_row[11], self.contact_1.suffix)
        self.assertEqual(self.split_row[12], self.contact_1.street_1)
        self.assertEqual(self.split_row[13], self.contact_1.street_2)
        self.assertEqual(self.split_row[14], self.contact_1.city)
        self.assertEqual(self.split_row[15], self.contact_1.state)
        self.assertEqual(self.split_row[16], self.contact_1.zip)
        self.assertEqual(self.split_row[25], "TEST_ID")

    def test_org_payee(self):
        self.assertEqual(self.split_row_org[6], self.contact_3.name)
        self.assertEqual(self.split_row_org[7], "")
        self.assertEqual(self.split_row_org[8], "")
        self.assertEqual(self.split_row_org[9], "")
        self.assertEqual(self.split_row_org[10], "")
        self.assertEqual(self.split_row_org[11], "")
        self.assertEqual(self.split_row_org[12], self.contact_3.street_1)
        self.assertEqual(self.split_row_org[13], self.contact_3.street_2)
        self.assertEqual(self.split_row_org[14], self.contact_3.city)
        self.assertEqual(self.split_row_org[15], self.contact_3.state)
        self.assertEqual(self.split_row_org[16], self.contact_3.zip)

    def test_election(self):
        self.assertEqual(self.split_row[17], "C2012")
        self.assertEqual(self.split_row[18], "OTHER DESCRIPTION")

    def test_expenditure(self):
        self.assertEqual(self.split_row[19], "20240115")
        self.assertEqual(self.split_row[20], "153.00")
        self.assertEqual(self.split_row[21], "20240112")
        self.assertEqual(self.split_row[22], "153.00")
        self.assertEqual(self.split_row[23], "EXPENDITURE DESCRIPTION")

    def test_category_code(self):
        self.assertEqual(self.split_row[24], "CODE")

    def test_support_oppose(self):
        self.assertEqual(self.split_row[26], "S")
        self.assertEqual(self.split_row[27], self.contact_2.candidate_id)
        self.assertEqual(self.split_row[28], self.contact_2.last_name)
        self.assertEqual(self.split_row[29], self.contact_2.first_name)
        self.assertEqual(self.split_row[30], self.contact_2.middle_name)
        self.assertEqual(self.split_row[31], self.contact_2.prefix)
        self.assertEqual(self.split_row[32], self.contact_2.suffix)
        self.assertEqual(self.split_row[33], self.contact_2.candidate_office)
        self.assertEqual(self.split_row[34], self.contact_2.candidate_district)
        self.assertEqual(self.split_row[35], self.contact_2.candidate_state)

    def test_completing(self):
        self.assertEqual(self.split_row[36], "LAST NAME")
        self.assertEqual(self.split_row[37], "FIRST NAME")
        self.assertEqual(self.split_row[38], "MIDDLE NAME")
        self.assertEqual(self.split_row[39], "Mr.")
        self.assertEqual(self.split_row[40], "Junior")

    def test_date_signed(self):
        today = datetime.today()
        formatted_date = today.strftime("%Y%m%d")
        self.assertEqual(self.split_row[41], formatted_date)

    def test_memo(self):
        self.assertEqual(self.split_row[42], "X")
        self.assertEqual(self.split_row[43], "MEMO TEXT DESCRIPTION")
