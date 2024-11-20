from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_report
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.reports.tests.utils import create_form1m
from datetime import datetime, timezone
from fecfiler.contacts.models import Contact
from fecfiler.web_services.models import UploadSubmission
import structlog

logger = structlog.get_logger(__name__)


class DotFECForm1MTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)

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

        self.candidate_2 = Contact.objects.create(
            type=Contact.ContactType.CANDIDATE,
            last_name="Candidate last 2",
            first_name="Candidate first 2",
            middle_name="Candidate middle 2",
            prefix="Mr. 2",
            suffix="Junior 2",
            committee_id=self.committee.committee_id,
            candidate_id="H8MA03132",
            candidate_office="H",
            candidate_state="MA",
            candidate_district="02",
        )

        self.candidate_3 = Contact.objects.create(
            type=Contact.ContactType.CANDIDATE,
            last_name="Candidate last 3",
            first_name="Candidate first 3",
            middle_name="Candidate middle 3",
            prefix="Mr. 3",
            suffix="Junior 3",
            committee_id=self.committee.committee_id,
            candidate_id="H8MA03133",
            candidate_office="H",
            candidate_state="MD",
            candidate_district="03",
        )

        self.candidate_4 = Contact.objects.create(
            type=Contact.ContactType.CANDIDATE,
            last_name="Candidate last 4",
            first_name="Candidate first 4",
            middle_name="Candidate middle 4",
            prefix="Mr. 4",
            suffix="Junior 4",
            committee_id=self.committee.committee_id,
            candidate_id="H8MA03134",
            candidate_office="H",
            candidate_state="KY",
            candidate_district="04",
        )

        self.candidate_5 = Contact.objects.create(
            type=Contact.ContactType.CANDIDATE,
            last_name="Candidate last 5",
            first_name="Candidate first 5",
            middle_name="Candidate middle 5",
            prefix="Mr. 5",
            suffix="Junior 5",
            committee_id=self.committee.committee_id,
            candidate_id="H8MA03135",
            candidate_office="H",
            candidate_state="NY",
            candidate_district="05",
        )

        self.f1m = create_form1m(self.committee)
        self.f1m.committee_name = "TEST_COMMITTEE"
        self.f1m.form_1m.committee_type = "A"
        self.f1m.form_1m.affiliated_date_form_f1_filed = datetime.strptime(
            "2024-01-01", "%Y-%m-%d"
        )
        self.f1m.form_1m.contact_affiliated = self.organization
        self.f1m.form_1m.contact_candidate_I = self.candidate
        self.f1m.form_1m.I_date_of_contribution = datetime.strptime(
            "2024-01-02", "%Y-%m-%d"
        )
        self.f1m.form_1m.contact_candidate_II = self.candidate_2
        self.f1m.form_1m.II_date_of_contribution = datetime.strptime(
            "2024-01-03", "%Y-%m-%d"
        )
        self.f1m.form_1m.contact_candidate_III = self.candidate_3
        self.f1m.form_1m.III_date_of_contribution = datetime.strptime(
            "2024-01-04", "%Y-%m-%d"
        )
        self.f1m.form_1m.contact_candidate_IV = self.candidate_4
        self.f1m.form_1m.IV_date_of_contribution = datetime.strptime(
            "2024-01-05", "%Y-%m-%d"
        )
        self.f1m.form_1m.contact_candidate_V = self.candidate_5
        self.f1m.form_1m.V_date_of_contribution = datetime.strptime(
            "2024-01-06", "%Y-%m-%d"
        )
        self.f1m.form_1m.date_of_51st_contributor = datetime.strptime(
            "2024-01-07", "%Y-%m-%d"
        )
        self.f1m.form_1m.date_of_original_registration = datetime.strptime(
            "2024-01-08", "%Y-%m-%d"
        )

        self.f1m.form_1m.date_committee_met_requirements = datetime.strptime(
            "2024-01-09", "%Y-%m-%d"
        )

        # Setup Address
        self.f1m.street_1 = "5313 Test Rd"
        self.f1m.street_2 = "Apt 1"
        self.f1m.city = "Phoenix"
        self.f1m.state = "AZ"
        self.f1m.zip = "85018"

        # Setup Treasurer
        self.f1m.treasurer_last_name = "Lastname"
        self.f1m.treasurer_first_name = "Firstname"
        self.f1m.treasurer_middle_name = "Middlename"
        self.f1m.treasurer_prefix = "Mr."
        self.f1m.treasurer_suffix = "Junior"

        upload_submission = UploadSubmission.objects.initiate_submission(self.f1m.id)
        self.f1m.upload_submission = upload_submission
        self.f1m.form_1m.save()
        self.f1m.save()

        report = compose_report(self.f1m.id, upload_submission.id)
        report_row = serialize_instance(report.get_form_name(), report)
        self.split_row = report_row.split(FS_STR)

    def test_form_type(self):
        for row in self.split_row:
            logger.debug(row)
        self.assertEqual(self.f1m.form_type, "F1MN")
        self.assertEqual(self.split_row[0], "F1MN")

    def test_committee_id(self):
        self.assertEqual(self.split_row[1], "C00000000")
        self.assertEqual(self.split_row[2], "TEST_COMMITTEE")
        self.assertEqual(self.split_row[8], "A")

    def test_address(self):
        self.assertEqual(self.split_row[3], "5313 Test Rd")
        self.assertEqual(self.split_row[4], "Apt 1")
        self.assertEqual(self.split_row[5], "Phoenix")
        self.assertEqual(self.split_row[6], "AZ")
        self.assertEqual(self.split_row[7], "85018")

    def test_affiliated(self):
        self.assertEqual(self.split_row[9], "20240101")
        self.assertEqual(self.split_row[10], str(self.organization.committee_id))
        self.assertEqual(self.split_row[11], "Test Org")

    def test_candidate_1(self):
        self.assertEqual(self.split_row[12], self.candidate.candidate_id)
        self.assertEqual(self.split_row[13], self.candidate.last_name)
        self.assertEqual(self.split_row[14], self.candidate.first_name)
        self.assertEqual(self.split_row[15], self.candidate.middle_name)
        self.assertEqual(self.split_row[16], self.candidate.prefix)
        self.assertEqual(self.split_row[17], self.candidate.suffix)
        self.assertEqual(self.split_row[18], self.candidate.candidate_office)
        self.assertEqual(self.split_row[19], self.candidate.candidate_state)
        self.assertEqual(self.split_row[20], self.candidate.candidate_district)
        self.assertEqual(self.split_row[21], "20240102")

    def test_candidate_2(self):
        self.assertEqual(self.split_row[22], self.candidate_2.candidate_id)
        self.assertEqual(self.split_row[23], self.candidate_2.last_name)
        self.assertEqual(self.split_row[24], self.candidate_2.first_name)
        self.assertEqual(self.split_row[25], self.candidate_2.middle_name)
        self.assertEqual(self.split_row[26], self.candidate_2.prefix)
        self.assertEqual(self.split_row[27], self.candidate_2.suffix)
        self.assertEqual(self.split_row[28], self.candidate_2.candidate_office)
        self.assertEqual(self.split_row[29], self.candidate_2.candidate_state)
        self.assertEqual(self.split_row[30], self.candidate_2.candidate_district)
        self.assertEqual(self.split_row[31], "20240103")

    def test_candidate_3(self):
        self.assertEqual(self.split_row[32], self.candidate_3.candidate_id)
        self.assertEqual(self.split_row[33], self.candidate_3.last_name)
        self.assertEqual(self.split_row[34], self.candidate_3.first_name)
        self.assertEqual(self.split_row[35], self.candidate_3.middle_name)
        self.assertEqual(self.split_row[36], self.candidate_3.prefix)
        self.assertEqual(self.split_row[37], self.candidate_3.suffix)
        self.assertEqual(self.split_row[38], self.candidate_3.candidate_office)
        self.assertEqual(self.split_row[39], self.candidate_3.candidate_state)
        self.assertEqual(self.split_row[40], self.candidate_3.candidate_district)
        self.assertEqual(self.split_row[41], "20240104")

    def test_candidate_4(self):
        self.assertEqual(self.split_row[42], self.candidate_4.candidate_id)
        self.assertEqual(self.split_row[43], self.candidate_4.last_name)
        self.assertEqual(self.split_row[44], self.candidate_4.first_name)
        self.assertEqual(self.split_row[45], self.candidate_4.middle_name)
        self.assertEqual(self.split_row[46], self.candidate_4.prefix)
        self.assertEqual(self.split_row[47], self.candidate_4.suffix)
        self.assertEqual(self.split_row[48], self.candidate_4.candidate_office)
        self.assertEqual(self.split_row[49], self.candidate_4.candidate_state)
        self.assertEqual(self.split_row[50], self.candidate_4.candidate_district)
        self.assertEqual(self.split_row[51], "20240105")

    def test_candidate_5(self):
        self.assertEqual(self.split_row[52], self.candidate_5.candidate_id)
        self.assertEqual(self.split_row[53], self.candidate_5.last_name)
        self.assertEqual(self.split_row[54], self.candidate_5.first_name)
        self.assertEqual(self.split_row[55], self.candidate_5.middle_name)
        self.assertEqual(self.split_row[56], self.candidate_5.prefix)
        self.assertEqual(self.split_row[57], self.candidate_5.suffix)
        self.assertEqual(self.split_row[58], self.candidate_5.candidate_office)
        self.assertEqual(self.split_row[59], self.candidate_5.candidate_state)
        self.assertEqual(self.split_row[60], self.candidate_5.candidate_district)
        self.assertEqual(self.split_row[61], "20240106")

    def test_dates(self):
        self.assertEqual(self.split_row[62], "20240107")
        self.assertEqual(self.split_row[63], "20240108")
        self.assertEqual(self.split_row[64], "20240109")

    def test_treasurer(self):
        self.assertEqual(self.split_row[65], "Lastname")
        self.assertEqual(self.split_row[66], "Firstname")
        self.assertEqual(self.split_row[67], "Middlename")
        self.assertEqual(self.split_row[68], "Mr.")
        self.assertEqual(self.split_row[69], "Junior")

    def test_date_signed(self):
        today = datetime.now(timezone.utc)
        formatted_date = today.strftime("%Y%m%d")
        self.assertEqual(self.split_row[70], formatted_date)
