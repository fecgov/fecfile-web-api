from django.test import TestCase
from unittest.mock import patch, MagicMock
from rest_framework.exceptions import ValidationError
from fecfiler.committee_accounts.committee_membership_utils import add_user_to_committee


class AddUserToCommitteeTests(TestCase):
    @patch("fecfiler.committee_accounts.committee_membership_utils.Membership")
    @patch("fecfiler.committee_accounts.committee_membership_utils.User")
    @patch("fecfiler.committee_accounts.committee_membership_utils.CommitteeAccount")
    def test_user_already_member_raises(
        self, mock_CommitteeAccount, mock_User, mock_Membership
    ):
        mock_Membership.objects.filter.return_value.count.return_value = 1
        with self.assertRaises(ValidationError) as ctx:
            add_user_to_committee("test@example.com", "C12345678", "ADMIN")
        self.assertIn("already a member", str(ctx.exception))
        mock_Membership.objects.filter.assert_called_once()

    @patch("fecfiler.committee_accounts.committee_membership_utils.Membership")
    @patch("fecfiler.committee_accounts.committee_membership_utils.User")
    @patch("fecfiler.committee_accounts.committee_membership_utils.CommitteeAccount")
    def test_committee_does_not_exist_raises(
        self, mock_CommitteeAccount, mock_User, mock_Membership
    ):
        mock_Membership.objects.filter.return_value.count.return_value = 0
        mock_User.objects.filter.return_value.first.return_value = MagicMock()
        mock_CommitteeAccount.objects.filter.return_value.first.return_value = None
        with self.assertRaises(ValidationError) as ctx:
            add_user_to_committee("test@example.com", "C00000000", "ADMIN")
        self.assertIn("does not exist", str(ctx.exception))
        mock_CommitteeAccount.objects.filter.assert_called_once_with(
            committee_id="C00000000"
        )

    @patch("fecfiler.committee_accounts.committee_membership_utils.Membership")
    @patch("fecfiler.committee_accounts.committee_membership_utils.User")
    @patch("fecfiler.committee_accounts.committee_membership_utils.CommitteeAccount")
    def test_add_user_to_committee_success(
        self, mock_CommitteeAccount, mock_User, mock_Membership
    ):
        mock_Membership.objects.filter.return_value.count.return_value = 0
        mock_user = MagicMock()
        mock_User.objects.filter.return_value.first.return_value = mock_user
        mock_committee = MagicMock()
        mock_CommitteeAccount.objects.filter.return_value.first.return_value = (
            mock_committee
        )
        mock_new_member = MagicMock()
        mock_Membership.return_value = mock_new_member

        add_user_to_committee("test@example.com", "C12345678", "ADMIN")
        mock_Membership.assert_called_once()
        mock_new_member.save.assert_called_once()

    @patch("fecfiler.committee_accounts.committee_membership_utils.Membership")
    @patch("fecfiler.committee_accounts.committee_membership_utils.User")
    @patch("fecfiler.committee_accounts.committee_membership_utils.CommitteeAccount")
    def test_add_pending_email_if_user_none(
        self, mock_CommitteeAccount, mock_User, mock_Membership
    ):
        mock_Membership.objects.filter.return_value.count.return_value = 0
        mock_User.objects.filter.return_value.first.return_value = None
        mock_committee = MagicMock()
        mock_CommitteeAccount.objects.filter.return_value.first.return_value = (
            mock_committee
        )
        mock_new_member = MagicMock()
        mock_Membership.return_value = mock_new_member

        add_user_to_committee("pending@example.com", "C12345678", "ADMIN")
        args, kwargs = mock_Membership.call_args
        self.assertIn("pending_email", kwargs)
        self.assertEqual(kwargs["pending_email"], None)
        mock_new_member.save.assert_called_once()
