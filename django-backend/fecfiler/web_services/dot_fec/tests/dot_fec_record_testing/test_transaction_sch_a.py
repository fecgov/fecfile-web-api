from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance, FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.transactions.tests.utils import create_schedule_a, create_transaction_memo
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.schedule_a.utils import add_schedule_a_contact_fields
from fecfiler.contacts.tests.utils import (
    create_test_candidate_contact,
    create_test_individual_contact,
    create_test_organization_contact,
    create_test_committee_contact,
)
from datetime import datetime


# Tests .FEC composition for SCHA records


class DotFECSchARecordsTestCase(TestCase):

    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        coverage_from = datetime.strptime("2024-01-01", "%Y-%m-%d")
        coverage_through = datetime.strptime("2024-02-01", "%Y-%m-%d")
        self.f3x = create_form3x(
            self.committee,
            coverage_from,
            coverage_through,
            {"L38_net_operating_expenditures_ytd": format(381.00, ".2f")},
        )

        self.contact_ind = create_test_individual_contact(
            "Last",
            "First",
            self.committee.id,
            {
                "middle_name": "Middle",
                "prefix": "Mr.",
                "suffix": "III",
                "street_1": "1234 Test Ln",
                "street_2": "Unit 321",
                "city": "Testville",
                "state": "AL",
                "zip": "12345",
                "employer": "Testerson Inc.",
                "occupation": "Tester",
                "telephone": "123-456-7890",
                "country": "USA",
            },
        )
        self.contact_org = create_test_organization_contact(
            "org name",
            self.committee.id,
            {
                "street_1": "41 Test Dr",
                "street_2": "Apt. B",
                "city": "Testopolis",
                "state": "CA",
                "zip": "54321",
                "telephone": "980-765-4321",
                "country": "USA",
            },
        )
        self.contact_com = create_test_committee_contact(
            "com name",
            "C01010101",
            self.committee.id,
            {
                "street_1": "45 Test Dr",
                "street_2": "Apt. A",
                "city": "Testopolis",
                "state": "CA",
                "zip": "54321",
                "telephone": "980-765-4321",
                "country": "USA",
            },
        )
        self.contact_can = create_test_candidate_contact(
            "Last",
            "First",
            self.committee.id,
            "S1AL00101",
            "S",
            "AL",
            "01",
            {
                "middle_name": "Middle",
                "prefix": "Mr.",
                "suffix": "III",
                "street_1": "1234 Test Ln",
                "street_2": "Unit 321",
                "city": "Testville",
                "state": "AL",
                "zip": "12345",
                "employer": "Testerson Inc.",
                "occupation": "Tester",
                "telephone": "123-456-7890",
                "country": "USA",
            },
        )

        trans_com_id = create_schedule_a(
            "JOINT_FUNDRAISING_TRANSFER",
            self.committee,
            self.contact_com,
            datetime.strptime("2024-01-06", "%Y-%m-%d"),
            "1.00",
            "GENERAL",
            "SA12",
        ).id
        trans_org_id = create_schedule_a(
            "PARTNERSHIP_JF_TRANSFER_MEMO",
            self.committee,
            self.contact_org,
            datetime.strptime("2024-01-07", "%Y-%m-%d"),
            "5.00",
            "GENERAL",
            "SA12",
            parent_id=trans_com_id,
        ).id
        trans_ind_id = create_schedule_a(
            "PARTNERSHIP_ATTRIBUTION_JF_TRANSFER_MEMO",
            self.committee,
            self.contact_ind,
            datetime.strptime("2024-01-08", "%Y-%m-%d"),
            "10.00",
            "GENERAL",
            "SA12",
            parent_id=trans_org_id,
        ).id
        trans_agg_id = create_schedule_a(
            "INDIVIDUAL_RECEIPT",
            self.committee,
            self.contact_ind,
            datetime.strptime("2024-01-09", "%Y-%m-%d"),
            "15.00",
            "GENERAL",
            "SA11AI",
            purpose_description="Testing Aggregate Transaction",
        ).id

        trans_donor = create_schedule_a(
            "EARMARK_MEMO",
            self.committee,
            self.contact_com,
            datetime.strptime("2024-01-21", "%Y-%m-%d"),
            "40.00",
            "GENERAL",
            "SA11AI",
            memo_code=True,
        )
        trans_donor.contact_2 = self.contact_can
        trans_donor.save()
        trans_donor_id = trans_donor.id
        create_transaction_memo(self.committee, trans_donor, "TRANSACTION_MEMO_TEXT")

        transaction_view_model = Transaction.objects.transaction_view().filter(
            committee_account__id=self.committee.id,
        )
        self.transaction_com = transaction_view_model.objects.get(id=trans_com_id)
        self.transaction_org = transaction_view_model.objects.get(id=trans_org_id)
        self.transaction_ind = transaction_view_model.objects.get(id=trans_ind_id)
        self.transaction_agg = transaction_view_model.objects.get(id=trans_agg_id)
        self.transaction_donor = transaction_view_model.objects.get(id=trans_donor_id)
        add_schedule_a_contact_fields(self.transaction_com)
        add_schedule_a_contact_fields(self.transaction_org)
        add_schedule_a_contact_fields(self.transaction_ind)
        add_schedule_a_contact_fields(self.transaction_agg)
        add_schedule_a_contact_fields(self.transaction_donor)

        self.transaction_com_row = serialize_instance("SchA", self.transaction_com).split(
            FS_STR
        )
        self.transaction_org_row = serialize_instance("SchA", self.transaction_org).split(
            FS_STR
        )
        self.transaction_ind_row = serialize_instance("SchA", self.transaction_ind).split(
            FS_STR
        )
        self.transaction_agg_row = serialize_instance("SchA", self.transaction_agg).split(
            FS_STR
        )
        self.transaction_donor_row = serialize_instance(
            "SchA", self.transaction_donor
        ).split(FS_STR)

    def test_form_name(self):
        self.assertEqual(self.transaction_ind_row[0], "SA12")
        self.assertEqual(self.transaction_org_row[0], "SA12")
        self.assertEqual(self.transaction_com_row[0], "SA12")
        self.assertEqual(self.transaction_agg_row[0], "SA11AII")

    def test_committee_id(self):
        self.assertEqual(self.transaction_ind_row[1], self.committee.committee_id)
        self.assertEqual(self.transaction_org_row[1], self.committee.committee_id)
        self.assertEqual(self.transaction_com_row[1], self.committee.committee_id)

    def test_transaction_id(self):
        self.assertEqual(self.transaction_ind_row[2], self.transaction_ind.transaction_id)
        self.assertEqual(self.transaction_org_row[2], self.transaction_org.transaction_id)
        self.assertEqual(self.transaction_com_row[2], self.transaction_com.transaction_id)

    def test_back_reference_fields(self):
        self.assertEqual(self.transaction_ind_row[3], self.transaction_org.transaction_id)
        self.assertEqual(self.transaction_org_row[3], self.transaction_com.transaction_id)
        self.assertEqual(self.transaction_com_row[3], "")

        # TODO: Skipped because this section is affected by a bug covered in Fecfile#1659
        # self.assertEqual(self.transaction_ind_row[4], "SA12")
        # self.assertEqual(self.transaction_org_row[4], "SA12")
        # self.assertEqual(self.transaction_com_row[4], '')

    def test_contact_fields(self):
        for contact, transaction_row in [
            [self.contact_ind, self.transaction_ind_row],
            [self.contact_org, self.transaction_org_row],
            [self.contact_com, self.transaction_com_row],
        ]:
            self.assertEqual(transaction_row[5], contact.type)
            self.assertEqual(transaction_row[6], contact.name or "")
            self.assertEqual(transaction_row[7], contact.last_name or "")
            self.assertEqual(transaction_row[8], contact.first_name or "")
            self.assertEqual(transaction_row[9], contact.middle_name or "")
            self.assertEqual(transaction_row[10], contact.prefix or "")
            self.assertEqual(transaction_row[11], contact.suffix or "")
            self.assertEqual(transaction_row[12], contact.street_1 or "")
            self.assertEqual(transaction_row[13], contact.street_2 or "")
            self.assertEqual(transaction_row[14], contact.city or "")
            self.assertEqual(transaction_row[15], contact.state or "")
            self.assertEqual(transaction_row[16], contact.zip or "")
            self.assertEqual(transaction_row[23], contact.employer or "")
            self.assertEqual(transaction_row[24], contact.occupation or "")

    def test_election_code_fields(self):
        self.assertEqual(self.transaction_ind_row[17], "")
        self.assertEqual(self.transaction_org_row[17], "")
        self.assertEqual(self.transaction_com_row[17], "")
        self.assertEqual(self.transaction_ind_row[18], "")
        self.assertEqual(self.transaction_org_row[18], "")
        self.assertEqual(self.transaction_com_row[18], "")

    def test_contribution_fields(self):
        self.assertEqual(self.transaction_ind_row[19], "20240108")
        self.assertEqual(self.transaction_org_row[19], "20240107")
        self.assertEqual(self.transaction_com_row[19], "20240106")
        self.assertEqual(self.transaction_agg_row[19], "20240109")
        self.assertEqual(self.transaction_ind_row[20], "10.00")
        self.assertEqual(self.transaction_org_row[20], "5.00")
        self.assertEqual(self.transaction_com_row[20], "1.00")
        self.assertEqual(self.transaction_agg_row[20], "15.00")
        self.assertEqual(self.transaction_ind_row[21], "10.00")
        self.assertEqual(self.transaction_org_row[21], "5.00")
        self.assertEqual(self.transaction_com_row[21], "1.00")
        self.assertEqual(self.transaction_agg_row[21], "25.00")
        self.assertEqual(self.transaction_agg_row[22], "Testing Aggregate Transaction")

    def test_donor_fields(self):
        self.assertEqual(self.transaction_donor_row[25], self.contact_com.committee_id)
        self.assertEqual(self.transaction_donor_row[26], self.contact_com.name)
        self.assertEqual(self.transaction_donor_row[27], self.contact_can.candidate_id)
        self.assertEqual(self.transaction_donor_row[28], self.contact_can.last_name)
        self.assertEqual(self.transaction_donor_row[29], self.contact_can.first_name)
        self.assertEqual(self.transaction_donor_row[30], self.contact_can.middle_name)
        self.assertEqual(self.transaction_donor_row[31], self.contact_can.prefix)
        self.assertEqual(self.transaction_donor_row[32], self.contact_can.suffix)
        self.assertEqual(
            self.transaction_donor_row[33], self.contact_can.candidate_office
        )
        self.assertEqual(self.transaction_donor_row[34], self.contact_can.candidate_state)
        self.assertEqual(
            self.transaction_donor_row[35], self.contact_can.candidate_district
        )

    def test_conduit_fields(self):
        # Conduit Fields are not (currently) populated for any SchA transactions

        self.assertEqual(self.transaction_donor_row[36], "")
        self.assertEqual(self.transaction_donor_row[37], "")
        self.assertEqual(self.transaction_donor_row[38], "")
        self.assertEqual(self.transaction_donor_row[39], "")
        self.assertEqual(self.transaction_donor_row[40], "")
        self.assertEqual(self.transaction_donor_row[41], "")

    def test_memo_code(self):
        self.assertEqual(self.transaction_ind_row[42], "")
        self.assertEqual(self.transaction_donor_row[42], "X")
