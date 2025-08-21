from django.test import TestCase
from unittest.mock import patch, MagicMock
from fecfiler.devops.utils.load_test_utils import LoadTestUtils


class LoadTestUtilsTestCase(TestCase):
    def setUp(self):
        self.utils = LoadTestUtils()

    @patch.object(LoadTestUtils, "create_load_test_committee_and_data")
    def test_create_load_test_committees_and_data(self, mock_create_committee_and_data):
        # Should call create_load_test_committee_and_data correct number of times
        # with correct args
        self.utils.create_load_test_committees_and_data(
            33333333, 3, 2, 4, 5, 0.5
        )
        self.assertEqual(mock_create_committee_and_data.call_count, 3)
        mock_create_committee_and_data.assert_any_call(
            "C33333333", 2, 4, 5, 0.5
        )
        mock_create_committee_and_data.assert_any_call(
            "C33333334", 2, 4, 5, 0.5
        )
        mock_create_committee_and_data.assert_any_call(
            "C33333335", 2, 4, 5, 0.5
        )

    @patch("fecfiler.devops.utils.load_test_utils.LocustDataGenerator")
    def test_create_load_test_committee_and_data(self, mock_locust_data_generator):
        mock_committee = MagicMock()
        mock_generator = MagicMock()
        mock_locust_data_generator.return_value = mock_generator
        with patch.object(
            self.utils, "create_new_committee", return_value=mock_committee
        ) as mock_create_new_committee:
            self.utils.create_load_test_committee_and_data(
                "C33333333", 2, 3, 4, 0.6
            )
            mock_create_new_committee.assert_called_once_with(
                "C33333333"
            )
            mock_generator.generate_form_3x.assert_called_once_with(2)
            mock_generator.generate_contacts.assert_called_once_with(3)
            mock_generator.generate_single_schedule_a_transactions.assert_called_once()
            mock_generator.generate_tiered_schedule_a_transactions.assert_called_once()

    @patch("fecfiler.devops.utils.load_test_utils.User")
    @patch("fecfiler.devops.utils.load_test_utils.CommitteeAccount")
    @patch("fecfiler.devops.utils.load_test_utils.Membership")
    def test_create_new_committee(
        self, mock_membership_model, mock_committee_account, mock_user_model
    ):
        mock_user = MagicMock()
        mock_user_model.objects.filter.return_value.first.return_value = mock_user
        mock_committee = MagicMock()
        mock_committee_account.objects.create.return_value = mock_committee
        mock_membership_model.objects.create.return_value = MagicMock()

        result = self.utils.create_new_committee("C33333333")
        self.assertEqual(result, mock_committee)
        mock_user_model.objects.filter.assert_called_once_with(
            email__iexact="test@test.com"
        )
        mock_committee_account.objects.create.assert_called_once_with(
            committee_id="C33333333"
        )
        mock_membership_model.objects.create.assert_called_once_with(
            role=mock_membership_model.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            committee_account_id=mock_committee.id,
            user=mock_user,
        )
