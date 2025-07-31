from django.test import TestCase
from unittest.mock import patch, MagicMock
from fecfiler.devops.utils.load_test_utils import LoadTestUtils


class LoadTestUtilsTestCase(TestCase):
    def setUp(self):
        self.utils = LoadTestUtils()

    @patch.object(LoadTestUtils, "create_load_test_committee_and_data")
    def test_create_load_test_committees_and_data(self, mock_create_committee_and_data):
        # Should call create_load_test_committee_and_data correct number of times with correct args
        self.utils.create_load_test_committees_and_data(
            "test@example.com", 3, 2, 4, 5, 0.5
        )
        self.assertEqual(mock_create_committee_and_data.call_count, 3)
        mock_create_committee_and_data.assert_any_call(
            "test@example.com", "C33333333", 2, 4, 5, 0.5
        )
        mock_create_committee_and_data.assert_any_call(
            "test@example.com", "C33333334", 2, 4, 5, 0.5
        )
        mock_create_committee_and_data.assert_any_call(
            "test@example.com", "C33333335", 2, 4, 5, 0.5
        )

    @patch("fecfiler.devops.utils.load_test_utils.LocustDataGenerator")
    def test_create_load_test_committee_and_data(self, mock_LocustDataGenerator):
        mock_committee = MagicMock()
        mock_generator = MagicMock()
        mock_LocustDataGenerator.return_value = mock_generator
        with patch.object(self.utils, "create_new_committee", return_value=mock_committee) as mock_create_new_committee:
            self.utils.create_load_test_committee_and_data(
                "test@example.com", "C33333333", 2, 3, 4, 0.6
            )
            mock_create_new_committee.assert_called_once_with("C33333333", "test@example.com")
            mock_generator.generate_form_3x.assert_called_once_with(2)
            mock_generator.generate_contacts.assert_called_once_with(3)
            mock_generator.generate_single_schedule_a_transactions.assert_called_once()
            mock_generator.generate_triple_schedule_a_transactions.assert_called_once()

    @patch("fecfiler.devops.utils.load_test_utils.User")
    @patch("fecfiler.devops.utils.load_test_utils.CommitteeAccount")
    @patch("fecfiler.devops.utils.load_test_utils.Membership")
    def test_create_new_committee(self, mock_Membership, mock_CommitteeAccount, mock_User):
        mock_user = MagicMock()
        mock_User.objects.filter.return_value.first.return_value = mock_user
        mock_committee = MagicMock()
        mock_CommitteeAccount.objects.create.return_value = mock_committee
        mock_membership = MagicMock()
        mock_Membership.objects.create.return_value = mock_membership

        result = self.utils.create_new_committee("C33333333", "test@example.com")
        self.assertEqual(result, mock_committee)
        mock_User.objects.filter.assert_called_once_with(email__iexact="test@example.com")
        mock_CommitteeAccount.objects.create.assert_called_once_with(committee_id="C33333333")
        mock_Membership.objects.create.assert_called_once_with(
            role=mock_Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            committee_account_id=mock_committee.id,
            user=mock_user,
        )
