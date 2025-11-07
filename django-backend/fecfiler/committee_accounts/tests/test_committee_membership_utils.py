from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.core.exceptions import ValidationError
from fecfiler.committee_accounts.models import Membership
from fecfiler.committee_accounts.utils.committee_membership import add_user_to_committee


class AddUserToCommitteeTests(TestCase):
    @patch("fecfiler.committee_accounts.committee_membership_utils.Membership")
    @patch("fecfiler.user.utils.User")
    @patch("fecfiler.committee_accounts.committee_membership_utils.CommitteeAccount")
    def test_user_already_member_raises(
        self, mock_committee_account, mock_user, mock_membership
    ):
        mock_membership.objects.filter.return_value.count.return_value = 1
        with self.assertRaises(ValidationError) as ctx:
            add_user_to_committee(
                "test@test.com",
                "C12345678",
                Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            )
        self.assertIn(
            "User with user_email is already a member of this committee",
            str(ctx.exception),
        )
        mock_membership.objects.filter.assert_called_once()

    @patch("fecfiler.committee_accounts.committee_membership_utils.Membership")
    @patch("fecfiler.user.utils.User")
    @patch("fecfiler.committee_accounts.committee_membership_utils.CommitteeAccount")
    def test_committee_does_not_exist_raises(
        self, mock_committee_account, mock_user, mock_membership
    ):
        mock_membership.objects.filter.return_value.count.return_value = 0
        mock_user.objects.filter.return_value.first.return_value = MagicMock()
        mock_committee_account.objects.filter.return_value.first.return_value = None
        with self.assertRaises(ValidationError) as ctx:
            add_user_to_committee(
                "test@test.com",
                "C00000000",
                Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            )
        self.assertIn("Committee with committee id does not exist", str(ctx.exception))
        mock_committee_account.objects.filter.assert_called_once_with(
            committee_id="C00000000"
        )

    @patch("fecfiler.committee_accounts.committee_membership_utils.Membership")
    @patch("fecfiler.user.utils.User")
    @patch("fecfiler.committee_accounts.committee_membership_utils.CommitteeAccount")
    def test_add_user_to_committee_success(
        self, mock_committee_account, mock_user, mock_membership
    ):
        mock_membership.objects.filter.return_value.count.return_value = 0
        mock_user.objects.filter.return_value.first.return_value = mock_user
        mock_committee = MagicMock()
        mock_committee_account.objects.filter.return_value.first.return_value = (
            mock_committee
        )
        mock_new_member = MagicMock()
        mock_membership.return_value = mock_new_member

        add_user_to_committee(
            "test@test.com", "C12345678", Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR
        )
        mock_membership.assert_called_once()
        mock_new_member.save.assert_called_once()

    @patch("fecfiler.committee_accounts.committee_membership_utils.Membership")
    @patch("fecfiler.user.utils.User")
    @patch("fecfiler.committee_accounts.committee_membership_utils.CommitteeAccount")
    def test_add_pending_email_if_user_none(
        self, mock_committee_account, mock_user, mock_membership
    ):
        mock_membership.objects.filter.return_value.count.return_value = 0
        mock_user.objects.filter.return_value.first.return_value = None
        mock_committee = MagicMock()
        mock_committee_account.objects.filter.return_value.first.return_value = (
            mock_committee
        )
        mock_new_member = MagicMock()
        mock_membership.return_value = mock_new_member

        add_user_to_committee(
            "test_pending@test.com",
            "C12345678",
            Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
        )
        _args, kwargs = mock_membership.call_args
        self.assertIn("pending_email", kwargs)
        self.assertEqual(kwargs["pending_email"], "test_pending@test.com")
        mock_new_member.save.assert_called_once()
