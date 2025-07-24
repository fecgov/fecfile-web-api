from django.test import TestCase
from unittest.mock import patch, MagicMock
from fecfiler.devops.utils.load_test_utils import LoadTestUtils


class LoadTestUtilsTestCase(TestCase):
    def setUp(self):
        self.utils = LoadTestUtils()

    @patch("fecfiler.devops.utils.load_test_utils.LocustDataGenerator")
    @patch.object(LoadTestUtils, "create_new_committee")
    @patch.object(LoadTestUtils, "create_reports")
    @patch.object(LoadTestUtils, "create_contacts")
    @patch.object(LoadTestUtils, "create_single_transactions")
    @patch.object(LoadTestUtils, "create_triple_transactions")
    def test_create_load_test_committee_and_data(
        self,
        mock_create_triple_transactions,
        mock_create_single_transactions,
        mock_create_contacts,
        mock_create_reports,
        create_new_committee,
        mock_locust_data_generator,
    ):
        mock_committee = MagicMock()
        create_new_committee.return_value = mock_committee
        mock_create_reports.return_value = [{id: "test_report_id"}]
        mock_create_contacts.return_value = [{id: "test_contact_id"}]
        mock_locust_data_generator.return_value = MagicMock()

        test_user_email = "test_user_email@test.com"
        test_new_committee_id = "C33333333"
        test_number_of_reports = 10
        test_number_of_contacts = 100
        test_number_of_transactions = 500
        test_single_to_triple_transaction_ratio = 9 / 10
        self.utils.create_load_test_committee_and_data(
            test_user_email,
            test_new_committee_id,
            test_number_of_reports,
            test_number_of_contacts,
            test_number_of_transactions,
            test_single_to_triple_transaction_ratio,
        )

        create_new_committee.assert_called_once()
        mock_create_reports.assert_called_once_with(test_number_of_reports)
        mock_create_contacts.assert_called_once_with(test_number_of_contacts)
        mock_create_single_transactions.assert_called_once()
        mock_create_triple_transactions.assert_called_once()

    @patch("fecfiler.devops.utils.load_test_utils.CommitteeAccount")
    @patch("fecfiler.devops.utils.load_test_utils.Membership")
    @patch("fecfiler.devops.utils.load_test_utils.User")
    def test_create_new_committee(
        self, mock_user, mock_membership, mock_committee_account
    ):
        test_new_committee_id = "C33333333"
        test_committee_id = "test_committee_id"
        test_user_email = "test_user_email@test.com"
        mock_committee = MagicMock()
        mock_committee.id = test_committee_id
        mock_committee_account.objects.create.return_value = mock_committee
        mock_user = MagicMock()
        mock_user.email = test_user_email
        mock_user.objects.filter.return_value = mock_user

        committee = self.utils.create_new_committee(
            test_new_committee_id, test_user_email
        )
        self.assertEqual(committee, mock_committee)
        mock_committee_account.objects.create.assert_called_once_with(
            committee_id=test_new_committee_id
        )
        mock_membership.objects.create.assert_called_once()

    @patch.object(LoadTestUtils, "locust_data_generator", create=True)
    def test_create_reports(self, mock_locust_data_generator):
        test_number_of_reports = 10
        test_reports = [{id: "test_report_id_1"}, {id: "test_report_id_2"}]
        mock_locust_data_generator.generate_form_3x.return_value = test_reports
        self.utils.locust_data_generator = mock_locust_data_generator
        result = self.utils.create_reports(test_number_of_reports)
        self.assertEqual(result, test_reports)
        mock_locust_data_generator.generate_form_3x.assert_called_once_with(
            test_number_of_reports
        )

    @patch("fecfiler.devops.utils.load_test_utils.Contact")
    @patch.object(LoadTestUtils, "locust_data_generator", create=True)
    def test_create_contacts(self, mock_locust_data_generator, mock_contact):
        test_number_of_contacts = 100
        mock_contact_objs = [MagicMock(), MagicMock()]
        mock_locust_data_generator.generate_contacts.return_value = mock_contact_objs
        mock_contact.objects.bulk_create.return_value = mock_contact_objs
        self.utils.locust_data_generator = mock_locust_data_generator
        result = self.utils.create_contacts(test_number_of_contacts)
        self.assertEqual(result, mock_contact_objs)
        mock_locust_data_generator.generate_contacts.assert_called_once_with(
            test_number_of_contacts
        )
        mock_contact.objects.bulk_create.assert_called_once_with(mock_contact_objs)

    @patch.object(LoadTestUtils, "locust_data_generator", create=True)
    def test_create_single_transactions(self, mock_locust_data_generator):
        test_number_of_transactions = 500
        test_reports = [{id: "test_report_1_id"}, {id: "test_report_2_id"}]
        test_contacts = [{id: "test_contact_1_id"}, {id: "test_contact_2_id"}]
        self.utils.locust_data_generator = mock_locust_data_generator
        self.utils.create_single_transactions(
            test_number_of_transactions, test_reports, test_contacts
        )
        mock_locust_data_generator.generate_single_transactions.assert_called_once_with(
            test_number_of_transactions, test_reports, test_contacts
        )

    @patch.object(LoadTestUtils, "locust_data_generator", create=True)
    def test_create_triple_transactions(self, mock_locust_data_generator):
        test_number_of_transactions = 500
        test_reports = [{id: "test_report_1_id"}, {id: "test_report_2_id"}]
        test_contacts = [{id: "test_contact_1_id"}, {id: "test_contact_2_id"}]
        self.utils.locust_data_generator = mock_locust_data_generator
        self.utils.create_triple_transactions(
            test_number_of_transactions, test_reports, test_contacts
        )
        mock_locust_data_generator.generate_triple_transactions.assert_called_once_with(
            test_number_of_transactions, test_reports, test_contacts
        )
