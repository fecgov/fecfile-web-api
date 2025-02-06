from django.test import TestCase
from fecfiler.web_services.dot_fec.dot_fec_serializer import serialize_instance
from fecfiler.web_services.dot_fec.dot_fec_composer import compose_report
from fecfiler.web_services.dot_fec.dot_fec_serializer import FS_STR
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.utils import create_committee_view
from fecfiler.reports.tests.utils import create_form3x
from fecfiler.contacts.tests.utils import create_test_individual_contact
from datetime import datetime
from fecfiler.web_services.models import UploadSubmission
import structlog

logger = structlog.get_logger(__name__)


class DotFECForm3XTestCase(TestCase):
    def setUp(self):
        self.committee = CommitteeAccount.objects.create(committee_id="C00000000")
        create_committee_view(self.committee.id)
        coverage_from = datetime.strptime("2024-01-01", "%Y-%m-%d")
        coverage_through = datetime.strptime("2024-02-01", "%Y-%m-%d")
        self.f3x = create_form3x(
            self.committee,
            coverage_from,
            coverage_through,
            {
                "change_of_address": True,
                "election_code": "H",
                "date_of_election": "2024-03-01",
                "state_of_election": "AZ",
                "qualified_committee": True,
                "L6b_cash_on_hand_beginning_period": format(1.00, ".2f"),
                "L6c_total_receipts_period": format(2.00, ".2f"),
                "L6d_subtotal_period": format(3.00, ".2f"),
                "L7_total_disbursements_period": format(4.00, ".2f"),
                "L8_cash_on_hand_at_close_period": format(5.00, ".2f"),
                "L9_debts_to_period": format(6.00, ".2f"),
                "L10_debts_by_period": format(7.00, ".2f"),
                "L11ai_itemized_period": format(8.00, ".2f"),
                "L11aii_unitemized_period": format(9.00, ".2f"),
                "L11aiii_total_period": format(10.00, ".2f"),
                "L11b_political_party_committees_period": format(11.00, ".2f"),
                "L11c_other_political_committees_pacs_period": format(12.00, ".2f"),
                "L11d_total_contributions_period": format(13.00, ".2f"),
                "L12_transfers_from_affiliated_other_party_cmtes_period": format(
                    14.00, ".2f"
                ),
                "L13_all_loans_received_period": format(15.00, ".2f"),
                "L14_loan_repayments_received_period": format(16.00, ".2f"),
                "L15_offsets_to_operating_expenditures_refunds_period": format(
                    17.00, ".2f"
                ),
                "L16_refunds_of_federal_contributions_period": format(18.00, ".2f"),
                "L17_other_federal_receipts_dividends_period": format(19.00, ".2f"),
                "L18a_transfers_from_nonfederal_account_h3_period": format(20.00, ".2f"),
                "L18b_transfers_from_nonfederal_levin_h5_period": format(21.00, ".2f"),
                "L18c_total_nonfederal_transfers_18a_18b_period": format(22.00, ".2f"),
                "L19_total_receipts_period": format(23.00, ".2f"),
                "L20_total_federal_receipts_period": format(24.00, ".2f"),
                "L21ai_federal_share_period": format(25.00, ".2f"),
                "L21aii_nonfederal_share_period": format(26.00, ".2f"),
                "L21b_other_federal_operating_expenditures_period": format(27.00, ".2f"),
                "L21c_total_operating_expenditures_period": format(28.00, ".2f"),
                "L22_transfers_to_affiliated_other_party_cmtes_period": format(
                    29.00, ".2f"
                ),
                "L23_contributions_to_federal_candidates_cmtes_period": format(
                    30.00, ".2f"
                ),
                "L24_independent_expenditures_period": format(31.00, ".2f"),
                "L25_coordinated_expend_made_by_party_cmtes_period": format(32.00, ".2f"),
                "L26_loan_repayments_period": format(33.00, ".2f"),
                "L27_loans_made_period": format(34.00, ".2f"),
                "L28a_individuals_persons_period": format(35.00, ".2f"),
                "L28b_political_party_committees_period": format(36.00, ".2f"),
                "L28c_other_political_committees_period": format(37.00, ".2f"),
                "L28d_total_contributions_refunds_period": format(38.00, ".2f"),
                "L29_other_disbursements_period": format(39.00, ".2f"),
                "L30ai_shared_federal_activity_h6_fed_share_period": format(40.00, ".2f"),
                "L30aii_shared_federal_activity_h6_nonfed_period": format(41.00, ".2f"),
                "L30b_nonallocable_fed_election_activity_period": format(42.00, ".2f"),
                "L30c_total_federal_election_activity_period": format(43.00, ".2f"),
                "L31_total_disbursements_period": format(44.00, ".2f"),
                "L32_total_federal_disbursements_period": format(45.00, ".2f"),
                "L33_total_contributions_period": format(46.00, ".2f"),
                "L34_total_contribution_refunds_period": format(47.00, ".2f"),
                "L35_net_contributions_period": format(48.00, ".2f"),
                "L36_total_federal_operating_expenditures_period": format(49.00, ".2f"),
                "L37_offsets_to_operating_expenditures_period": format(50.00, ".2f"),
                "L38_net_operating_expenditures_ytd": format(51.00, ".2f"),
            },
        )
        self.f3x.committee_name = "TEST_COMMITTEE"

        # Setup Address
        self.f3x.street_1 = "5313 E Osborne Rd"
        self.f3x.street_2 = "Apt 1"
        self.f3x.city = "Phoenix"
        self.f3x.state = "AZ"
        self.f3x.zip = "85018"

        # Setup Treasurer
        self.f3x.treasurer_last_name = "Lastname"
        self.f3x.treasurer_first_name = "Firstname"
        self.f3x.treasurer_middle_name = "Middlename"
        self.f3x.treasurer_prefix = "Mr."
        self.f3x.treasurer_suffix = "Junior"
        self.f3x.save()

        UploadSubmission.objects.initiate_submission(self.f3x.id)
        self.f3x.refresh_from_db()

        self.contact_1 = create_test_individual_contact(
            "last name", "First name", self.committee.id
        )

        report = compose_report(self.f3x.id)
        report_row = serialize_instance(report.get_form_name(), report)
        self.split_row = report_row.split(FS_STR)

    def test_form_type(self):
        self.assertEqual(self.f3x.form_type, "F3XN")
        for row in self.split_row:
            logger.debug(row)
        self.assertEqual(self.split_row[0], "F3XN")

    def test_committee_id(self):
        self.assertEqual(self.split_row[1], "C00000000")
        self.assertEqual(self.split_row[2], "TEST_COMMITTEE")

    def test_change_of_address(self):
        self.assertEqual(self.split_row[3], "X")

    def test_address(self):
        self.assertEqual(self.split_row[4], "5313 E Osborne Rd")
        self.assertEqual(self.split_row[5], "Apt 1")
        self.assertEqual(self.split_row[6], "Phoenix")
        self.assertEqual(self.split_row[7], "AZ")
        self.assertEqual(self.split_row[8], "85018")

    def test_report_code(self):
        self.assertEqual(self.split_row[9], "Q1")

    def test_election(self):
        self.assertEqual(self.split_row[10], "H")
        self.assertEqual(self.split_row[11], "20240301")
        self.assertEqual(self.split_row[12], "AZ")

    def test_coverage(self):
        self.assertEqual(self.split_row[13], "20240101")
        self.assertEqual(self.split_row[14], "20240201")

    def test_qualified_committee(self):
        self.assertEqual(self.split_row[15], "X")

    def test_treasurer(self):
        self.assertEqual(self.split_row[16], "Lastname")
        self.assertEqual(self.split_row[17], "Firstname")
        self.assertEqual(self.split_row[18], "Middlename")
        self.assertEqual(self.split_row[19], "Mr.")
        self.assertEqual(self.split_row[20], "Junior")

    def test_date_signed(self):
        """Because date_signed is timezoned to the server
        the test date needs to be in the same timezone"""
        today = datetime.now()
        formatted_date = today.strftime("%Y%m%d")
        self.assertEqual(self.split_row[21], formatted_date)

    def test_column_a(self):
        self.assertEqual(self.split_row[22], "1.00")
        self.assertEqual(self.split_row[23], "2.00")
        self.assertEqual(self.split_row[24], "3.00")
        self.assertEqual(self.split_row[25], "4.00")
        self.assertEqual(self.split_row[26], "5.00")
        self.assertEqual(self.split_row[27], "6.00")
        self.assertEqual(self.split_row[28], "7.00")
        self.assertEqual(self.split_row[29], "8.00")
        self.assertEqual(self.split_row[30], "9.00")
        self.assertEqual(self.split_row[31], "10.00")
        self.assertEqual(self.split_row[32], "11.00")
        self.assertEqual(self.split_row[33], "12.00")
        self.assertEqual(self.split_row[34], "13.00")
        self.assertEqual(self.split_row[35], "14.00")
        self.assertEqual(self.split_row[36], "15.00")
        self.assertEqual(self.split_row[37], "16.00")
        self.assertEqual(self.split_row[38], "17.00")
        self.assertEqual(self.split_row[39], "18.00")
        self.assertEqual(self.split_row[40], "19.00")
        self.assertEqual(self.split_row[41], "20.00")
        self.assertEqual(self.split_row[42], "21.00")
        self.assertEqual(self.split_row[43], "22.00")
        self.assertEqual(self.split_row[44], "23.00")
        self.assertEqual(self.split_row[45], "24.00")
        self.assertEqual(self.split_row[46], "25.00")
        self.assertEqual(self.split_row[47], "26.00")
        self.assertEqual(self.split_row[48], "27.00")
        self.assertEqual(self.split_row[49], "28.00")
        self.assertEqual(self.split_row[50], "29.00")
        self.assertEqual(self.split_row[51], "30.00")
        self.assertEqual(self.split_row[52], "31.00")
        self.assertEqual(self.split_row[53], "32.00")
        self.assertEqual(self.split_row[54], "33.00")
        self.assertEqual(self.split_row[55], "34.00")
        self.assertEqual(self.split_row[56], "35.00")
        self.assertEqual(self.split_row[57], "36.00")
        self.assertEqual(self.split_row[58], "37.00")
        self.assertEqual(self.split_row[59], "38.00")
        self.assertEqual(self.split_row[60], "39.00")
        self.assertEqual(self.split_row[61], "40.00")
        self.assertEqual(self.split_row[62], "41.00")
        self.assertEqual(self.split_row[63], "42.00")
        self.assertEqual(self.split_row[64], "43.00")
        self.assertEqual(self.split_row[65], "44.00")
        self.assertEqual(self.split_row[66], "45.00")
        self.assertEqual(self.split_row[67], "46.00")
        self.assertEqual(self.split_row[68], "47.00")
        self.assertEqual(self.split_row[69], "48.00")
        self.assertEqual(self.split_row[70], "49.00")
        self.assertEqual(self.split_row[71], "50.00")
        self.assertEqual(self.split_row[-1], "51.00")

    def test_column_b(self):
        for i in range(72, 121):
            self.assertEqual(self.split_row[i], "")
