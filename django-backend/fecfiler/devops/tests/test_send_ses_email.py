from botocore.exceptions import ClientError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from unittest.mock import patch

from fecfiler.email import send_email_notification


class SesEmailHelperTestCase(TestCase):
    @patch("fecfiler.email.SES_CLIENT")
    @patch("fecfiler.email.SES_DOMAIN", "example.com")
    def test_send_email_notification_happy_path(self, ses_client_mock):
        ses_client_mock.send_email.return_value = {"MessageId": "test-message-id"}

        response = send_email_notification(
            to_email="recipient@example.com",
            subject="Test Subject",
            body_text="Hello from SES",
            from_user="sender",
        )

        self.assertEqual(response["MessageId"], "test-message-id")
        ses_client_mock.send_email.assert_called_once_with(
            FromEmailAddress="sender@example.com",
            Destination={"ToAddresses": ["recipient@example.com"]},
            Content={
                "Simple": {
                    "Subject": {"Data": "Test Subject"},
                    "Body": {"Text": {"Data": "Hello from SES"}},
                }
            },
        )

    @patch("fecfiler.email.SES_CLIENT", None)
    def test_send_email_notification_requires_ses_client(self):
        with self.assertRaisesMessage(
            RuntimeError,
            "SES client is not configured",
        ):
            send_email_notification(
                to_email="recipient@example.com",
                subject="Test Subject",
                body_text="Hello from SES",
                from_user="sender",
            )


class SendSesEmailCommandTestCase(TestCase):
    @patch("fecfiler.devops.management.commands.send_ses_email.send_email_notification")
    @patch(
        "fecfiler.devops.management.commands.send_ses_email.SES_FROM_EMAIL",
        "default-sender@example.com"
    )
    def test_command_uses_default_sender(self, send_email_notification_mock):
        send_email_notification_mock.return_value = {"MessageId": "message-id-123"}

        call_command("send_ses_email", "recipient@example.com", "test body")

        send_email_notification_mock.assert_called_once_with(
            to_email="recipient@example.com",
            subject="FECFile SES PoC notification",
            body_text="test body",
            from_user=None,
        )

    @patch("fecfiler.devops.management.commands.send_ses_email.send_email_notification")
    @patch("fecfiler.devops.management.commands.send_ses_email.SES_FROM_EMAIL", None)
    def test_command_uses_from_email_override(self, send_email_notification_mock):
        send_email_notification_mock.return_value = {"MessageId": "message-id-123"}

        call_command(
            "send_ses_email",
            "recipient@example.com",
            "test body",
            from_user="override-sender",
            subject="custom subject",
        )

        send_email_notification_mock.assert_called_once_with(
            to_email="recipient@example.com",
            subject="custom subject",
            body_text="test body",
            from_user="override-sender",
        )

    @patch("fecfiler.devops.management.commands.send_ses_email.SES_FROM_EMAIL", None)
    def test_command_requires_sender_configuration(self):
        with self.assertRaisesMessage(
            CommandError,
            "No sender configured",
        ):
            call_command("send_ses_email", "recipient@example.com", "test body")

    @patch("fecfiler.devops.management.commands.send_ses_email.send_email_notification")
    @patch(
        "fecfiler.devops.management.commands.send_ses_email.SES_FROM_EMAIL",
        "default-sender@example.com"
    )
    def test_command_surfaces_ses_errors(self, send_email_notification_mock):
        send_email_notification_mock.side_effect = ClientError(
            {
                "Error": {
                    "Code": "MessageRejected",
                    "Message": "Address is not verified.",
                }
            },
            "SendEmail",
        )

        with self.assertRaisesMessage(CommandError, "Failed to send SES email"):
            call_command("send_ses_email", "recipient@example.com", "test body")
