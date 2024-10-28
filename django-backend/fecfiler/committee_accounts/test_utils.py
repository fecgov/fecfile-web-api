from django.test import TestCase
from fecfiler.committee_accounts.utils import (
    create_committee_account,
    check_email_match,
    get_committee_account_data_from_test_efo,
)

from fecfiler.user.models import User
from django.core.management import call_command
from unittest.mock import Mock, patch


class CommitteeAccountsUtilsTest(TestCase):

    def setUp(self):
        with patch("fecfiler.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            call_command("load_committee_data")
            self.test_user = User.objects.create(email="test@fec.gov", username="gov")
            self.other_user = User.objects.create(email="test@fec.com", username="com")
            self.create_error_message = "could not create committee account"

    # create_committee_account

    def test_create_committee_account(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            account = create_committee_account("C12345678", self.test_user)
            self.assertEquals(account.committee_id, "C12345678")

    def test_create_committee_account_existing(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            account = create_committee_account("C12345678", self.test_user)
            self.assertEquals(account.committee_id, "C12345678")
            self.assertRaisesMessage(
                Exception,
                self.create_error_message,
                create_committee_account,
                committee_id="C12345678",
                user=self.test_user,
            )

    def test_create_committee_account_mismatch_email(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            self.assertRaisesMessage(
                Exception,
                self.create_error_message,
                create_committee_account,
                committee_id="C12345678",
                user=self.other_user,
            )

    def test_create_committee_account_unauthorized_email(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            self.assertRaisesMessage(
                Exception,
                self.create_error_message,
                create_committee_account,
                committee_id="C12345678",
                user=User.objects.create(
                    email="test@unauthorized_domain.com", username="unauthorized_domeain"
                ),
            )

    def test_create_committee_account_case_insensitive(self):
        with patch("fecfiler.committee_accounts.utils.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            self.test_user.email = self.test_user.email.upper()
            account = create_committee_account("C12345678", self.test_user)
            self.assertEquals(account.committee_id, "C12345678")
            self.assertRaisesMessage(
                Exception,
                self.create_error_message,
                create_committee_account,
                committee_id="C12345678",
                user=self.test_user,
            )

    # check_email_match

    def test_no_f1_email(self):
        result = check_email_match("email3@example.com", None)
        self.assertEqual(result, "No email provided in F1")

    def test_no_match(self):
        f1_emails = "email1@example.com;email2@example.com"
        result = check_email_match("email3@example.com", f1_emails)
        self.assertEqual(
            result, "Email email3@example.com does not match committee email"
        )

    def test_match_semicolon(self):
        f1_emails = "email1@example.com;email2@example.com"
        result = check_email_match("email1@example.com", f1_emails)
        self.assertIsNone(result)
        result = check_email_match("email2@example.com", f1_emails)
        self.assertIsNone(result)

    def test_match_comma(self):
        f1_emails = "email1@example.com,email2@example.com"
        result = check_email_match("email2@example.com", f1_emails)
        self.assertIsNone(result)

    def test_email_matching_case_insensitive(self):
        f1_emails = "email1@example.com;email2@example.com"
        result = check_email_match("EMAIL1@example.com", f1_emails)
        self.assertIsNone(result)

    """
    RETRIEVE COMMITTEE DATA TESTS
    """

    def mock_requests_get(self, mock_requests, status_code, committee_data):
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = {"results": [committee_data]}
        mock_requests.get = Mock()
        mock_requests.get.return_value = mock_response

    def test_get_committee_account_data_from_test_efo_PAC(self):  # noqa N802
        with patch("fecfiler.committee_accounts.utils.requests") as mock_requests:
            test_efo_committee_data = {
                "committee_id": "C12345678",
                "email": "test@test.com",
                "committee_type": "A",
                "treasurer_first_name": "Treasurer First",
                "committee_str1": "Committee Street 1",
                "committee_name": "Committee Name",
            }
            self.mock_requests_get(mock_requests, 200, test_efo_committee_data)
            committee_account_data = get_committee_account_data_from_test_efo("C12345678")

            self.assertEqual(
                committee_account_data.get("committee_type_label"),
                "PAC - Qualified - Unauthorized",
            )
            self.assertEqual(committee_account_data.get("isPAC"), True)
            self.assertEqual(committee_account_data.get("isPTY"), False)
            self.assertEqual(committee_account_data.get("qualified"), True)
            self.assertEqual(committee_account_data.get("filing_frequency"), "Q")
            self.assertEqual(committee_account_data.get("name"), "Committee Name")
            self.assertEqual(
                committee_account_data.get("treasurer_name_1"), "Treasurer First"
            )
            self.assertEqual(committee_account_data.get("street_1"), "Committee Street 1")

    def test_get_committee_account_data_from_test_efo_PTY(self):  # noqa N802
        with patch("fecfiler.committee_accounts.utils.requests") as mock_requests:
            test_efo_committee_data = {
                "committee_id": "C12345678",
                "email": "test@test.com",
                "committee_type": "D",
                "treasurer_first_name": "Treasurer First",
                "committee_str1": "Committee Street 1",
                "committee_name": "Committee Name",
            }
            self.mock_requests_get(mock_requests, 200, test_efo_committee_data)
            committee_account_data = get_committee_account_data_from_test_efo("C12345678")

            self.assertEqual(
                committee_account_data.get("committee_type_label"),
                "Party - Qualified - Unauthorized",
            )
            self.assertEqual(committee_account_data.get("isPAC"), False)
            self.assertEqual(committee_account_data.get("isPTY"), True)
            self.assertEqual(committee_account_data.get("qualified"), True)
            self.assertEqual(committee_account_data.get("filing_frequency"), "Q")
            self.assertEqual(committee_account_data.get("name"), "Committee Name")
            self.assertEqual(
                committee_account_data.get("treasurer_name_1"), "Treasurer First"
            )
            self.assertEqual(committee_account_data.get("street_1"), "Committee Street 1")
