from django.test import TestCase
from fecfiler.committee_accounts.utils.accounts import (
    create_committee_account,
    delete_committee_account,
    check_user_email_matches_committee_email,
    get_committee_account_data,
    get_committee_emails,
    get_production_committee_emails,
    get_test_committee_emails,
    get_eligible_report_types_raw,
    get_eligible_report_types_processed,
)

from fecfiler.user.models import User
from fecfiler.contacts.models import Contact
from fecfiler.reports.models import Report
from fecfiler.transactions.models import Transaction
from django.core.management import call_command
from unittest.mock import Mock, patch


class CommitteeAccountsUtilsTest(TestCase):

    def setUp(self):
        with patch("fecfiler.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            call_command("load_mocked_committee_data")
            self.test_user = User.objects.create(email="test@fec.gov", username="gov")
            self.other_user = User.objects.create(email="test@fec.com", username="com")
            self.create_error_message = "could not create committee account"

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

    # create_committee_account

    def test_create_committee_account(self):
        with patch("fecfiler.committee_accounts.utils.accounts.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            account = create_committee_account("C12345678", self.test_user)
            self.assertEqual(account.committee_id, "C12345678")

    def test_create_committee_account_existing(self):
        with patch("fecfiler.committee_accounts.utils.accounts.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            account = create_committee_account("C12345678", self.test_user)
            self.assertEqual(account.committee_id, "C12345678")
            self.assertRaisesMessage(
                Exception,
                "Committee account already exists",
                create_committee_account,
                committee_id="C12345678",
                user=self.test_user,
            )

    def test_create_committee_account_mismatch_email(self):
        with patch("fecfiler.committee_accounts.utils.accounts.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            self.assertRaisesMessage(
                Exception,
                "User email does not match committee email",
                create_committee_account,
                committee_id="C12345678",
                user=self.other_user,
            )

    def test_create_committee_account_case_insensitive(self):
        with patch("fecfiler.committee_accounts.utils.accounts.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            self.test_user.email = self.test_user.email.upper()
            account = create_committee_account("C12345678", self.test_user)
            self.assertEqual(account.committee_id, "C12345678")
            self.assertRaisesMessage(
                Exception,
                "Committee account already exists",
                create_committee_account,
                committee_id="C12345678",
                user=self.test_user,
            )

    # delete_committee_account

    def test_delete_committee_account(self):
        with patch("fecfiler.committee_accounts.utils.accounts.settings") as settings:
            settings.FLAG__COMMITTEE_DATA_SOURCE = "MOCKED"
            account = create_committee_account("C12345678", self.test_user)
            self.assertEqual(account.committee_id, "C12345678")
            report = account.report_set.create()
            transaction = report.transactions.create(committee_account=account)
            transaction.contact_1 = Contact.objects.create(committee_account=account)
            transaction.save()
            self.assertEqual(Report.objects.filter(committee_account=account).count(), 1)
            self.assertEqual(
                Transaction.objects.filter(committee_account=account).count(), 1
            )
            self.assertEqual(Contact.objects.filter(committee_account=account).count(), 1)
            delete_committee_account("C12345678")
            self.assertEqual(Report.objects.filter(committee_account=account).count(), 0)
            self.assertEqual(
                Transaction.objects.filter(committee_account=account).count(), 0
            )
            self.assertEqual(Contact.objects.filter(committee_account=account).count(), 0)

    # check_user_email_matches_committee_email

    def test_no_f1_email(self):
        result = check_user_email_matches_committee_email("email3@example.com", None)
        self.assertEqual(result, False)

    def test_no_match(self):
        f1_emails = "email1@example.com;email2@example.com"
        result = check_user_email_matches_committee_email("email3@example.com", f1_emails)
        self.assertEqual(result, False)

    def test_match_semicolon(self):
        f1_emails = "email1@example.com;email2@example.com"
        result = check_user_email_matches_committee_email("email1@example.com", f1_emails)
        self.assertEqual(result, True)
        result = check_user_email_matches_committee_email("email2@example.com", f1_emails)
        self.assertEqual(result, True)

    def test_match_comma(self):
        f1_emails = "email1@example.com,email2@example.com"
        result = check_user_email_matches_committee_email("email2@example.com", f1_emails)
        self.assertEqual(result, True)

    def test_email_matching_case_insensitive(self):
        f1_emails = "email1@example.com;email2@example.com"
        result = check_user_email_matches_committee_email("EMAIL1@example.com", f1_emails)
        self.assertEqual(result, True)

    """
    GET COMMITTEE EMAILS
    """

    def test_get_emails_environments(self):
        with (
            patch("fecfiler.committee_accounts.utils.accounts.settings") as settings,
            patch(
                "fecfiler.committee_accounts.utils.accounts"
                ".get_production_committee_emails"
            ) as get_production_committee_emails,
            patch(
                "fecfiler.committee_accounts.utils.accounts" ".get_test_committee_emails"
            ) as get_test_committee_emails,
            patch(
                "fecfiler.committee_accounts.utils.accounts.get_mocked_committee_emails"
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
        with patch("fecfiler.shared.utilities.requests") as mock_requests:
            production_committee_data = {
                "email": "list_of_emails",
                "committee_type": "D",
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
            self.assertEqual(production_emails, None)

    def test_get_test_committee_emails(self):
        with patch("fecfiler.shared.utilities.requests") as mock_requests:
            test_committee_data = {
                "email": "list_of_emails",
            }
            self.mock_requests_get(
                mock_requests, self.mock_response(200, test_committee_data)
            )
            test_emails = get_test_committee_emails("C12345678")
            self.assertEqual(test_emails, "list_of_emails")
            # test when the endpoint has no data
            self.mock_requests_get(mock_requests, self.mock_response(200, None))
            test_emails = get_test_committee_emails("C12345678")
            self.assertEqual(test_emails, "")

    """
    RETRIEVE COMMITTEE DATA TESTS
    """

    def test_get_committee_account_data_from_test_PAC(self):  # noqa N802
        with (
            patch("fecfiler.shared.utilities.requests") as mock_requests,
            patch("fecfiler.committee_accounts.utils.accounts.settings") as settings,
        ):
            settings.FLAG__COMMITTEE_DATA_SOURCE = "TEST"
            test_efo_committee_data = {
                "committee_id": "C12345678",
                "email": "test@test.com",
                "committee_type": "A",
                "candidate_office": "H",
                "treasurer_first_name": "Treasurer First",
                "committee_str1": "Committee Street 1",
                "committee_name": "Committee Name",
            }
            self.mock_requests_get(
                mock_requests, self.mock_response(200, test_efo_committee_data)
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
            self.assertEqual(
                committee_account_data.get("eligible_report_types"), ["F3", "F99"]
            )

    def test_get_committee_account_data_from_test_PTY(self):  # noqa N802
        with (
            patch("fecfiler.shared.utilities.requests") as mock_requests,
            patch("fecfiler.committee_accounts.utils.accounts.settings") as settings,
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
                mock_requests, self.mock_response(200, test_efo_committee_data)
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

    def test_get_committee_account_data_from_production_processed(self):
        with (
            patch("fecfiler.shared.utilities.requests") as mock_requests,
            patch("fecfiler.committee_accounts.utils.accounts.settings") as settings,
        ):
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            production_committee_data = {
                "committee_id": "C12345678",
                "email": "email",
                "committee_type": "Q",
                "committee_type_full": "Qualified Leadership PAC",
                "designation": "D",
            }
            self.mock_requests_get(
                mock_requests, self.mock_response(200, production_committee_data)
            )
            committee_account_data = get_committee_account_data("C12345678")
            self.assertEqual(
                committee_account_data.get("committee_type_label"),
                "Qualified Leadership PAC",
            )
            self.assertEqual(committee_account_data.get("isPAC"), True)
            self.assertEqual(committee_account_data.get("isPTY"), False)
            self.assertEqual(committee_account_data.get("qualified"), True)

    def test_get_committee_account_data_with_candidate_info_production_processed(self):
        with (
            patch("fecfiler.shared.utilities.requests") as mock_requests,
            patch("fecfiler.committee_accounts.utils.accounts.settings") as settings,
        ):
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            production_committee_data = {
                "committee_id": "C12345678",
                "email": "email",
                "committee_type": "H",
                "committee_type_full": "House",
                "designation": "A",
            }
            test_candidate_office = 'test_candidate_office'
            test_candidate_state = 'DC'
            test_candidate_district = '2'
            self.mock_requests_get(
                mock_requests,
                [
                    self.mock_response(200, production_committee_data),
                    self.mock_response(200, {
                        "office": test_candidate_office,
                        "state": test_candidate_state,
                        "district_number": test_candidate_district,
                    }),
                ],
            )
            committee_account_data = get_committee_account_data("C12345678")
            self.assertEqual(
                committee_account_data.get("candidate_office"), test_candidate_office
            )
            self.assertEqual(
                committee_account_data.get("candidate_state"), test_candidate_state
            )
            self.assertEqual(
                committee_account_data.get("candidate_district"), test_candidate_district
            )

    def test_get_committee_account_data_from_production_processed_pac_pty(self):
        with (
            patch("fecfiler.shared.utilities.requests") as mock_requests,
            patch("fecfiler.committee_accounts.utils.accounts.settings") as settings,
        ):
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            production_committee_data = {
                "committee_id": "C12345678",
                "email": "email",
                "committee_type": "X",
                "committee_type_full": "Party - Non-qualified",
                "designation": "U",
            }
            self.mock_requests_get(
                mock_requests, self.mock_response(200, production_committee_data)
            )
            committee_account_data = get_committee_account_data("C12345678")
            self.assertEqual(
                committee_account_data.get("committee_type_label"),
                "Party - Non-qualified",
            )
            self.assertEqual(committee_account_data.get("isPAC"), True)
            self.assertEqual(committee_account_data.get("isPTY"), True)
            self.assertEqual(committee_account_data.get("qualified"), False)

    def test_get_committee_account_data_from_production_raw(self):
        with (
            patch("fecfiler.shared.utilities.requests") as mock_requests,
            patch("fecfiler.committee_accounts.utils.accounts.settings") as settings,
        ):
            settings.FLAG__COMMITTEE_DATA_SOURCE = "PRODUCTION"
            production_committee_data = {
                "committee_id": "C12345678",
                "email": "email",
                "committee_type": "D",
                "designation": "D",
            }
            # no response in processed endpoint and data in raw endpoint
            self.mock_requests_get(
                mock_requests,
                [
                    self.mock_response(200, None),
                    self.mock_response(200, production_committee_data),
                ],
            )
            committee_account_data = get_committee_account_data("C12345678")
            self.assertEqual(
                committee_account_data.get("committee_type_label"),
                "Non-qualified",
            )
            self.assertEqual(committee_account_data.get("isPAC"), True)
            self.assertEqual(committee_account_data.get("isPTY"), True)
            self.assertEqual(committee_account_data.get("qualified"), False)

    def test_get_eligible_report_types_raw(self):
        test_committee_data_A_H = {
            "committee_type": "A",
            "candidate_office": "H",
        }
        eligible_types_A_H = get_eligible_report_types_raw(test_committee_data_A_H)
        self.assertEqual(eligible_types_A_H, ["F3", "F99"])

        test_committee_data_B_S = {
            "committee_type": "B",
            "candidate_office": "S",
        }
        eligible_types_B_S = get_eligible_report_types_raw(test_committee_data_B_S)
        self.assertEqual(eligible_types_B_S, ["F3", "F99"])

        test_committee_data_A_P = {
            "committee_type": "A",
            "candidate_office": "P",
        }
        eligible_types_A_P = get_eligible_report_types_raw(test_committee_data_A_P)
        self.assertEqual(eligible_types_A_P, ["F99"])

        test_committee_data_C = {
            "committee_type": "C",
        }
        eligible_types_C = get_eligible_report_types_raw(test_committee_data_C)
        self.assertEqual(eligible_types_C, ["F3X", "F24", "F1M", "F99"])

        test_committee_data_FOO = {
            "committee_type": "FOO",
        }
        eligible_types_FOO = get_eligible_report_types_raw(test_committee_data_FOO)
        self.assertEqual(eligible_types_FOO, ["F99"])

        test_committee_data_None = {
            "committee_type": None,
        }
        eligible_types_None = get_eligible_report_types_raw(test_committee_data_None)
        self.assertEqual(eligible_types_None, ["F99"])

        test_committee_data_invalid = None
        eligible_types_invalid = get_eligible_report_types_raw(
            test_committee_data_invalid
        )
        self.assertEqual(eligible_types_invalid, ["F99"])

    def test_get_eligible_report_types_processed(self):
        test_committee_data_AH = {
            "designation": "A",
            "committee_type": "H",
        }
        eligible_types_AH = get_eligible_report_types_processed(test_committee_data_AH)
        self.assertEqual(eligible_types_AH, ["F3", "F99"])

        test_committee_data_JS = {
            "designation": "J",
            "committee_type": "S",
        }
        eligible_types_JS = get_eligible_report_types_processed(test_committee_data_JS)
        self.assertEqual(eligible_types_JS, ["F3", "F99"])

        test_committee_data_BN = {
            "designation": "B",
            "committee_type": "N",
        }

        eligible_types_BN = get_eligible_report_types_processed(test_committee_data_BN)
        self.assertEqual(eligible_types_BN, ["F3X", "F24", "F1M", "F99"])

        test_committee_data_BO = {
            "designation": "B",
            "committee_type": "O",
        }
        eligible_types_BO = get_eligible_report_types_processed(test_committee_data_BO)
        self.assertEqual(eligible_types_BO, ["F3X", "F24", "F1M", "F99"])

        test_committee_data_BQ = {
            "designation": "B",
            "committee_type": "Q",
        }
        eligible_types_BQ = get_eligible_report_types_processed(test_committee_data_BQ)
        self.assertEqual(eligible_types_BQ, ["F3X", "F24", "F1M", "F99"])

        test_committee_data_BV = {
            "designation": "B",
            "committee_type": "V",
        }
        eligible_types_BV = get_eligible_report_types_processed(test_committee_data_BV)
        self.assertEqual(eligible_types_BV, ["F3X", "F24", "F1M", "F99"])

        test_committee_data_BW = {
            "designation": "B",
            "committee_type": "W",
        }
        eligible_types_BW = get_eligible_report_types_processed(test_committee_data_BW)
        self.assertEqual(eligible_types_BW, ["F3X", "F24", "F1M", "F99"])

        test_committee_data_UQ = {
            "designation": "U",
            "committee_type": "Q",
        }

        eligible_types_UQ = get_eligible_report_types_processed(test_committee_data_UQ)
        self.assertEqual(eligible_types_UQ, ["F3X", "F24", "F1M", "F99"])

        test_committee_data_non_existant = {
            "designation": "Z",
            "committee_type": "Z",
        }

        eligible_types_non_existant = get_eligible_report_types_processed(
            test_committee_data_non_existant
        )
        self.assertEqual(eligible_types_non_existant, ["F99"])

        test_committee_data_invalid = None

        eligible_types_invalid = get_eligible_report_types_processed(
            test_committee_data_invalid
        )
        self.assertEqual(eligible_types_invalid, ["F99"])
