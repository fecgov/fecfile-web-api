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

    @patch("fecfiler.email.SES_CLIENT")
    @patch("fecfiler.email.SES_DOMAIN", "example.com")
    def test_send_email_notification_html_happy_path(self, ses_client_mock):
        ses_client_mock.send_email.return_value = {"MessageId": "test-message-id"}

        response = send_email_notification(
            to_email="recipient@example.com",
            subject="Test Subject",
            body_text="Hello from SES",
            body_html="<p>Hello from SES</p>",
            from_user="sender",
        )

        self.assertEqual(response["MessageId"], "test-message-id")
        ses_client_mock.send_email.assert_called_once_with(
            FromEmailAddress="sender@example.com",
            Destination={"ToAddresses": ["recipient@example.com"]},
            Content={
                "Simple": {
                    "Subject": {"Data": "Test Subject"},
                    "Body": {
                        "Text": {"Data": "Hello from SES"},
                        "Html": {"Data": "<p>Hello from SES</p>"},
                    },
                }
            },
        )

    @patch("fecfiler.email.SES_CLIENT", None)
    def test_send_email_notification_requires_ses_client(self):
        with self.assertRaisesMessage(
            RuntimeError,
            "SES client is not available",
        ):
            send_email_notification(
                to_email="recipient@example.com",
                subject="Test Subject",
                body_text="Hello from SES",
                from_user="sender",
            )
