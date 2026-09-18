from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from unittest.mock import patch


class DeleteLocustLoadTestDataCommandTest(TestCase):
    @patch(
        "fecfiler.devops.management.commands"
        ".delete_locust_load_test_data.LoadTestUtils"
    )
    def test_command_runs_when_load_mirror_validation_passes(self, mock_load_test_utils):
        call_command("delete_locust_load_test_data")

        mock_load_test_utils.return_value.validate_load_mirror_runtime \
            .assert_called_once()
        mock_load_test_utils.return_value.delete_load_test_committees_and_data \
            .assert_called_once()

    @patch(
        "fecfiler.devops.management.commands"
        ".delete_locust_load_test_data.LoadTestUtils"
    )
    def test_command_errors_when_load_mirror_validation_fails(self, mock_load_test_utils):
        mock_load_test_utils.return_value.validate_load_mirror_runtime.side_effect = (
            ValueError(
                "delete_locust_load_test_data can only be run on a load testing mirror"
            )
        )

        with self.assertRaisesRegex(CommandError, "load testing mirror"):
            call_command("delete_locust_load_test_data")

        mock_load_test_utils.return_value \
            .delete_load_test_committees_and_data.assert_not_called()
