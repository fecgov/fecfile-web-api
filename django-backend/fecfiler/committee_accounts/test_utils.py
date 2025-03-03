from django.test import TestCase
from fecfiler.committee_accounts.utils import (
    create_committee_account,
    check_email_match,
    get_committee_from_test_fec,
    get_committee_account_data,
    get_committee_emails,
    get_production_committee_emails,
    get_test_committee_emails,
    get_mocked_committee_emails,
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
    GET COMMITTEE EMAILS
    """

    def test_get_emails_enfironments(self):
        with (
            patch("fecfiler.committee_accounts.utils.settings") as settings,
            patch(
                "fecfiler.committee_accounts.utils.get_production_committee_emails"
            ) as get_production_committee_emails,
            patch(
                "fecfiler.committee_accounts.utils.get_test_committee_emails"
            ) as get_test_committee_emails,
            patch(
                "fecfiler.committee_accounts.utils.get_mocked_committee_emails"
            ) as get_mocked_committee_emails,
        ):
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            get_committee_emails("C12345678")
            self.assertTrue(get_mocked_committee_emails.called)
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            get_committee_emails("C12345678")
            self.assertTrue(get_test_committee_emails.called)
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            get_committee_emails("C12345678")
            self.assertTrue(get_production_committee_emails.called)

    def test_get_production_committee_emails(self):
        with patch("fecfiler.committee_accounts.utils.requests") as mock_requests:
            production_committee_data = {
                "email": "list_of_emails",
            }
            # test when the raw endpoint has nothing and the processed endpoint has data
            self.mock_requests_get(
                mock_requests,
                [
                    self.mock_response(200, None),
                    self.mock_response(200, production_committee_data),
                ],
            )
            production_emails = get_production_committee_emails("C12345678")
            self.assertEqual(production_emails, "list_of_emails")
            # test when the raw endpoint has data
            self.mock_requests_get(
                mock_requests,
                [
                    self.mock_response(200, production_committee_data),
                    self.mock_response(200, None),
                ],
            )
            production_emails = get_production_committee_emails("C12345678")
            self.assertEqual(production_emails, "list_of_emails")
            # test when neither endpoint has data
            self.mock_requests_get(
                mock_requests,
                [
                    self.mock_response(200, None),
                    self.mock_response(200, None),
                ],
            )
            production_emails = get_production_committee_emails("C12345678")
            self.assertEqual(production_emails, "")

    """
    RETRIEVE COMMITTEE DATA TESTS
    """

    def mock_requests_get(self, mock_requests, responses):
        mock_requests.get = Mock()
        mock_requests.get.side_effect = (
            responses if isinstance(responses, list) else [responses]
        )

    def mock_response(self, status_code, committee_data):
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.json.return_value = {
            "results": [committee_data] if committee_data else []
        }
        return mock_response

    def test_get_committee_account_data_from_test_efo_PAC(self):  # noqa N802
        with (
            patch("fecfiler.committee_accounts.utils.requests") as mock_requests,
            patch("fecfiler.committee_accounts.utils.settings") as settings,
        ):
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            test_efo_committee_data = {
                "committee_id": "C12345678",
                "email": "test@test.com",
                "committee_type": "A",
                "treasurer_first_name": "Treasurer First",
                "committee_str1": "Committee Street 1",
                "committee_name": "Committee Name",
            }
            self.mock_requests_get(
                mock_requests, 200, self.mock_response(200, test_efo_committee_data)
            )
            committee_account_data = get_committee_account_data("C12345678")

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
        with (
            patch("fecfiler.committee_accounts.utils.requests") as mock_requests,
            patch("fecfiler.committee_accounts.utils.settings") as settings,
        ):
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            test_efo_committee_data = {
                "committee_id": "C12345678",
                "email": "test@test.com",
                "committee_type": "D",
                "treasurer_first_name": "Treasurer First",
                "committee_str1": "Committee Street 1",
                "committee_name": "Committee Name",
            }
            self.mock_requests_get(
                mock_requests, 200, self.mock_response(test_efo_committee_data)
            )
            committee_account_data = get_committee_account_data("C12345678")

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
