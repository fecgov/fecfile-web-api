from django.test import TestCase
from unittest.mock import patch, MagicMock
from fecfiler.user.models import User
from fecfiler.user.utils import (
    get_user_by_email_or_id,
    delete_active_sessions_for_user_and_committee,
    disable_user,
    reset_security_consent_date,
)
from uuid import uuid4
from django.core.management import call_command
from django.core.management.base import CommandError
import datetime
import structlog

logger = structlog.get_logger(__name__)


class UserUtilsTestCase(TestCase):
    def setUp(self):
        self.user_1 = User.objects.create_user(
            email="test_user_1@test.com", user_id=str(uuid4())
        )
        self.user_2 = User.objects.create_user(
            email="test_user_2@test.com", user_id=str(uuid4())
        )
        self.user_3 = User.objects.create_user(
            email="test_user_3@test.com",
            user_id=str(uuid4(), security_consent_exp_date=datetime.datetime.today()),
        )

    def test_get_user_with_invalid_strings(self):
        self.assertEqual(get_user_by_email_or_id(""), None)
        self.assertEqual(get_user_by_email_or_id("test_user_4@test.com"), None)
        self.assertEqual(get_user_by_email_or_id("test_user_1ATtest.com"), None)
        self.assertEqual(get_user_by_email_or_id("-"), None)
        self.assertEqual(
            get_user_by_email_or_id(str(self.user_1.id).replace("-", "")), None
        )

    def test_get_user_with_valid_strings(self):
        self.assertEqual(get_user_by_email_or_id(str(self.user_1.id)), self.user_1)
        self.assertEqual(get_user_by_email_or_id(self.user_1.email), self.user_1)
        self.assertEqual(get_user_by_email_or_id(self.user_2.email), self.user_2)
        self.assertEqual(get_user_by_email_or_id(str(self.user_3.id)), self.user_3)

    def test_disable_user_email(self, use="method"):
        # get the test user
        user = get_user_by_email_or_id(self.user_1.email)
        self.assertTrue(user.is_active)

        # disable the test user
        if use == "command":
            try:
                call_command("disable_user", email=user.email)
            except Exception as e:
                print(f"Error running command: {e}")
        else:
            disable_user(None, user.email)

        # re-get the test user
        user = get_user_by_email_or_id(self.user_1.email)
        self.assertFalse(user.is_active)

    def test_disable_user_uuid(self, use="method"):
        # get the test user
        user = get_user_by_email_or_id(str(self.user_1.id))
        self.assertTrue(user.is_active)

        # disable the test user
        if use == "command":
            try:
                call_command("disable_user", uuid=user.id)
            except Exception as e:
                print(f"Error running command: {e}")
        else:
            disable_user(str(user.id), None)

        # re-get the test user
        user = get_user_by_email_or_id(str(self.user_1.id))
        self.assertFalse(user.is_active)

    def test_disable_user_email_command(self):
        self.test_disable_user_email(use="command")

    def test_disable_user_uuid_command(self):
        self.test_disable_user_uuid(use="command")

    def test_disable_user_command_missing_arg(self):
        with self.assertRaises(CommandError) as cm:
            call_command("disable_user")

        self.assertIn(
            "one of the arguments --uuid --email is required", str(cm.exception)
        )

    def test_reset_security_consent_date_with_email(self, use="method"):
        self.assertIsNotNone(self.user_3.security_consent_exp_date)
        if use == "comand":
            call_command("reset_security_consent_date", self.user_3.email)
        else:
            reset_security_consent_date(self.user_3.email)
        self.test_user.refresh_from_db()
        self.assertIsNone(self.user_3.security_consent_exp_date)

    def test_reset_security_consent_date_with_wrong_email(self, use="method"):
        self.assertIsNotNone(self.user_3.security_consent_exp_date)
        if use == "command":
            call_command("reset_security_consent_date", "t@fec.gov")
        else:
            reset_security_consent_date("t@fec.gov")
        self.user_3.refresh_from_db()
        self.assertIsNotNone(self.user_3.security_consent_exp_date)

    def test_reset_security_consent_date_with_email_command(self):
        self.test_reset_with_email(use="command")

    def test_reset_security_consent_date_with_wrong_email_command(self):
        self.test_reset_with_wrong_email(use="command")

    # delete_active_sessions_for_user_and_committee

    @patch("fecfiler.user.utils.Session")
    @patch("fecfiler.user.utils.datetime")
    def test_delete_active_sessions_for_user_and_committee_missing_params(
        self, mock_datetime, mock_session_model
    ):
        mock_session = MagicMock()
        mock_session.get_decoded.return_value = {
            "_auth_user_id": "test_user_id_1",
            "committee_id": "test_committee_id_1",
        }
        mock_session_model.objects.filter.return_value = [mock_session]

        delete_active_sessions_for_user_and_committee("", "test_committee_id_1")
        mock_session.delete.assert_not_called()

        delete_active_sessions_for_user_and_committee("test_user_id_1", "")
        mock_session.delete.assert_not_called()

    @patch("fecfiler.user.utils.Session")
    @patch("fecfiler.user.utils.datetime")
    def test_delete_active_sessions_for_user_and_committee_no_match(
        self, mock_datetime, mock_session_model
    ):
        mock_session = MagicMock()
        mock_session.get_decoded.return_value = {
            "_auth_user_id": "test_user_id_1",
            "committee_id": "test_committee_id_1",
        }
        mock_session_model.objects.filter.return_value = [mock_session]

        delete_active_sessions_for_user_and_committee(
            "test_user_id_2", "test_committee_id_2"
        )

        mock_session.delete.assert_not_called()

    @patch("fecfiler.user.utils.Session")
    @patch("fecfiler.user.utils.datetime")
    def test_delete_active_sessions_for_user_and_committee_happy_path(
        self, mock_datetime, mock_session_model
    ):
        session_to_delete_1 = MagicMock()
        session_to_delete_2 = MagicMock()
        session_to_leave_different_user = MagicMock()
        session_to_leave_different_committee = MagicMock()
        """
        Delete these
        """
        session_to_delete_1.get_decoded.return_value = {
            "_auth_user_id": "user_to_delete",
            "committee_id": "committee_to_delete",
        }
        # another session to confirm both get deleted
        session_to_delete_2.get_decoded.return_value = {
            "_auth_user_id": "user_to_delete",
            "committee_id": "committee_to_delete",
        }

        """
        Leave the following alone
        """
        # correct committee but different user
        session_to_leave_different_user.get_decoded.return_value = {
            "_auth_user_id": "other_user",
            "committee_id": "committee_to_delete",
        }
        #
        session_to_leave_different_committee.get_decoded.return_value = {
            "_auth_user_id": "user_to_delete",
            "committee_id": "other_committee",
        }
        mock_session_model.objects.filter.return_value = [
            session_to_delete_1,
            session_to_delete_2,
            session_to_leave_different_user,
            session_to_leave_different_committee,
        ]

        delete_active_sessions_for_user_and_committee(
            "user_to_delete", "committee_to_delete"
        )

        session_to_delete_1.delete.assert_called_once()
        session_to_delete_2.delete.assert_called_once()
        session_to_leave_different_user.delete.assert_not_called()
        session_to_leave_different_committee.delete.assert_not_called()
