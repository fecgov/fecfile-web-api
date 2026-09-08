from django.test import TestCase
from unittest.mock import patch, MagicMock
from fecfiler.devops.utils.load_test import LoadTestUtils
from fecfiler.committee_accounts.models import CommitteeAccount, Membership
from fecfiler.user.models import User
import json


class LoadTestUtilsTestCase(TestCase):
    def setUp(self):
        self.utils = LoadTestUtils()

    @patch.object(LoadTestUtils, "create_load_test_committee_and_data")
    def test_create_load_test_committees_and_data(self, mock_create_committee_and_data):
        # Should call create_load_test_committee_and_data correct number of times
        # with correct args
        self.utils.create_load_test_committees_and_data(
            33333333, 3, 2, 3, 4, 2, 2, 1, 1, 0.6, 5
        )
        self.assertEqual(mock_create_committee_and_data.call_count, 3)
        mock_create_committee_and_data.assert_any_call(
            "C33333333", 2, 3, 4, 2, 2, 1, 1, 0.6, 5
        )
        mock_create_committee_and_data.assert_any_call(
            "C33333334", 2, 3, 4, 2, 2, 1, 1, 0.6, 5
        )
        mock_create_committee_and_data.assert_any_call(
            "C33333335", 2, 3, 4, 2, 2, 1, 1, 0.6, 5
        )

    @patch("fecfiler.devops.utils.load_test.LocustDataGenerator")
    def test_create_load_test_committee_and_data(self, mock_locust_data_generator):
        mock_committee = MagicMock()
        mock_generator = MagicMock()
        mock_locust_data_generator.return_value = mock_generator
        with patch.object(
            self.utils, "create_new_committee", return_value=mock_committee
        ) as mock_create_new_committee:
            self.utils.create_load_test_committee_and_data(
                "C33333333", 2, 3, 4, 2, 2, 1, 1, 0.6, 5
            )
            mock_create_new_committee.assert_called_once_with(
                "C33333333"
            )
            mock_generator.generate_form_3x.assert_called_once_with(2)
            mock_generator.generate_contacts.assert_called_once_with(3)
            mock_generator.generate_single_schedule_a_transactions.assert_called_once()
            mock_generator.generate_tiered_schedule_a_transactions.assert_called_once()

    @patch("fecfiler.devops.utils.load_test.User")
    @patch("fecfiler.devops.utils.load_test.CommitteeAccount")
    @patch("fecfiler.devops.utils.load_test.Membership")
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

    @patch.dict(
        "os.environ",
        {
            "VCAP_APPLICATION": json.dumps(
                {
                    "application_name": "load-fecfile-web-api",
                }
            ),
            "VCAP_SERVICES": json.dumps(
                {
                    "aws-rds": [
                        {"name": "load-fecfile-api-rds"},
                    ],
                    "s3": [
                        {"name": "load-fecfile-api-s3"},
                    ],
                }
            ),
        },
        clear=False,
    )
    def test_validate_load_mirror_runtime_success(self):
        self.utils.validate_load_mirror_runtime()

    @patch.dict(
        "os.environ",
        {
            "VCAP_APPLICATION": json.dumps(
                {
                    "application_name": "fecfile-web-api",
                }
            ),
            "VCAP_SERVICES": json.dumps(
                {
                    "aws-rds": [
                        {"name": "load-fecfile-api-rds"},
                    ],
                    "s3": [
                        {"name": "load-fecfile-api-s3"},
                    ],
                }
            ),
        },
        clear=False,
    )
    def test_validate_load_mirror_runtime_fails_for_non_load_app(self):
        with self.assertRaisesRegex(ValueError, "load testing mirror"):
            self.utils.validate_load_mirror_runtime()

    @patch.dict(
        "os.environ",
        {
            "VCAP_APPLICATION": json.dumps(
                {
                    "application_name": "load-fecfile-web-api",
                }
            ),
            "VCAP_SERVICES": json.dumps(
                {
                    "aws-rds": [
                        {"name": "fecfile-api-rds"},
                    ],
                    "s3": [
                        {"name": "load-fecfile-api-s3"},
                    ],
                }
            ),
        },
        clear=False,
    )
    def test_validate_load_mirror_runtime_fails_without_required_rds(self):
        with self.assertRaisesRegex(ValueError, "load testing mirror"):
            self.utils.validate_load_mirror_runtime()

    @patch.dict(
        "os.environ",
        {
            "VCAP_APPLICATION": json.dumps(
                {
                    "application_name": "load-fecfile-web-api",
                }
            ),
            "VCAP_SERVICES": json.dumps(
                {
                    "aws-rds": [
                        {"name": "load-fecfile-api-rds"},
                    ],
                }
            ),
        },
        clear=False,
    )
    def test_validate_load_mirror_runtime_succeeds_with_only_required_rds(self):
        self.utils.validate_load_mirror_runtime()

    @patch.dict(
        "os.environ",
        {
            "VCAP_APPLICATION": json.dumps(
                {
                    "application_name": "load-fecfile-web-api",
                }
            ),
            "VCAP_SERVICES": "not-json",
        },
        clear=False,
    )
    def test_validate_load_mirror_runtime_fails_for_invalid_service_json(self):
        with self.assertRaisesRegex(ValueError, "Could not parse VCAP_SERVICES"):
            self.utils.validate_load_mirror_runtime()

    def test_delete_load_test_committees_and_data_deletes_only_marked_data(self):
        load_user = User.objects.create(
            email="test@test.com",
            username="test@test.com",
        )
        keep_user = User.objects.create(
            email="keep@example.com",
            username="keep@example.com",
        )

        load_committee = CommitteeAccount.objects.create(committee_id="C33333333")
        keep_committee = CommitteeAccount.objects.create(committee_id="C12345678")

        Membership.objects.create(
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            committee_account=load_committee,
            user=load_user,
        )
        Membership.objects.create(
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            committee_account=keep_committee,
            user=keep_user,
        )

        self.utils.delete_load_test_committees_and_data()

        self.assertFalse(
            CommitteeAccount.all_objects.filter(committee_id="C33333333").exists()
        )
        self.assertTrue(
            CommitteeAccount.all_objects.filter(committee_id="C12345678").exists()
        )
        self.assertFalse(User.objects.filter(email__iexact="test@test.com").exists())
        self.assertTrue(User.objects.filter(email__iexact="keep@example.com").exists())

    def test_delete_load_test_committees_and_data_keeps_test_user_with_memberships(self):
        load_user = User.objects.create(
            email="test@test.com",
            username="test@test.com",
        )
        committee = CommitteeAccount.objects.create(committee_id="C33333333")
        other_committee = CommitteeAccount.objects.create(committee_id="C87654321")

        Membership.objects.create(
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            committee_account=committee,
            user=load_user,
        )
        Membership.objects.create(
            role=Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            committee_account=other_committee,
            user=load_user,
        )

        with patch.object(
            LoadTestUtils,
            "delete_load_test_committees_and_data",
            wraps=self.utils.delete_load_test_committees_and_data,
        ):
            CommitteeAccount.objects.filter(committee_id="C33333333") \
                .first().hard_delete()
            self.utils.delete_orphaned_test_user()

        self.assertTrue(User.objects.filter(email__iexact="test@test.com").exists())
