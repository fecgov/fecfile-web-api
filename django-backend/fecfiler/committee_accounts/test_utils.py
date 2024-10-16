from unittest.mock import patch
from django.test import TestCase
from fecfiler.committee_accounts.utils import (
    create_committee_account,
    check_email_match,
)

from fecfiler.user.models import User
from django.core.management import call_command


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
