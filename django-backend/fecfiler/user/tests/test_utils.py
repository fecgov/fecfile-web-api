from django.test import TestCase
from unittest.mock import patch, MagicMock
from fecfiler.user.models import User
from fecfiler.user.utils import (
    get_user_by_email_or_id,
    delete_active_sessions_for_user_and_committee,
)
from uuid import uuid4


class UserUtilsTestCase(TestCase):
    def setUp(self):
        self.user_1 = User.objects.create_user(
            email="test_user_1@test.com", user_id=str(uuid4())
        )
        self.user_2 = User.objects.create_user(
            email="test_user_2@test.com", user_id=str(uuid4())
        )
        self.user_3 = User.objects.create_user(
            email="test_user_3@test.com", user_id=str(uuid4())
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

    # delete_active_sessions_for_user_and_committee

    @patch("fecfiler.user.utils.Session")
    @patch("fecfiler.user.utils.datetime")
    def test_delete_active_sessions_for_user_and_committee_missing_params(
        self, mock_datetime, mock_Session
    ):
        mock_session = MagicMock()
        mock_session.get_decoded.return_value = {
            "_auth_user_id": "test_user_id_1",
            "committee_id": "test_committee_id_1",
        }
        mock_Session.objects.filter.return_value = [mock_session]

        delete_active_sessions_for_user_and_committee("", "test_committee_id_1")
        mock_session.delete.assert_not_called()

        delete_active_sessions_for_user_and_committee("test_user_id_1", "")
        mock_session.delete.assert_not_called()

    @patch("fecfiler.user.utils.Session")
    @patch("fecfiler.user.utils.datetime")
    def test_delete_active_sessions_for_user_and_committee_no_match(
        self, mock_datetime, mock_Session
    ):
        mock_session = MagicMock()
        mock_session.get_decoded.return_value = {
            "_auth_user_id": "test_user_id_1",
            "committee_id": "test_committee_id_1",
        }
        mock_Session.objects.filter.return_value = [mock_session]

        delete_active_sessions_for_user_and_committee(
            "test_user_id_2", "test_committee_id_2"
        )

        mock_session.delete.assert_not_called()

    @patch("fecfiler.user.utils.Session")
    @patch("fecfiler.user.utils.datetime")
    def test_delete_active_sessions_for_user_and_committee_happy_path(
        self, mock_datetime, mock_Session
    ):
        mock_session_1 = MagicMock()
        mock_session_2 = MagicMock()
        mock_session_3 = MagicMock()
        mock_session_1.get_decoded.return_value = {
            "_auth_user_id": "test_user_id_1",
            "committee_id": "test_committee_id_1",
        }
        mock_session_2.get_decoded.return_value = {
            "_auth_user_id": "test_user_id_2",
            "committee_id": "test_committee_id_2",
        }
        mock_session_3.get_decoded.return_value = {
            "_auth_user_id": "test_user_id_3",
            "committee_id": "test_committee_id_3",
        }
        mock_Session.objects.filter.return_value = [
            mock_session_1,
            mock_session_2,
            mock_session_3,
        ]

        delete_active_sessions_for_user_and_committee(
            "test_user_id_1", "test_committee_id_1"
        )

        mock_session_1.delete.assert_called_once()
        mock_session_2.delete.assert_not_called()
        mock_session_3.delete.assert_not_called()
