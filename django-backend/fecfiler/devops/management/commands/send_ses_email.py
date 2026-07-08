from django.core.management.base import CommandError
from fecfiler.devops.management.commands.fecfile_base import FECCommand, Levels
from fecfiler.email import send_email_notification
from fecfiler.settings import SES_FROM_EMAIL
import structlog

logger = structlog.get_logger(__name__)


class Command(FECCommand):
    help = "Send a plaintext email with AWS SES v2"
    command_name = "send_ses_email"

    def add_arguments(self, parser):
        parser.add_argument(
            "to_email",
            type=str,
            help="The email address that should receive the message",
        )
        parser.add_argument(
            "message",
            type=str,
            help="The plaintext message body to send",
        )
        parser.add_argument(
            "--subject",
            type=str,
            default="FECFile SES PoC notification",
            help="Optional email subject",
        )
        parser.add_argument(
            "--from-user",
            dest="from_user",
            type=str,
            default=None,
            help=(
                "Optional sender email username override, used with service domain. "
                "Defaults to SES_FROM_USER setting."
            ),
        )

    def command(self, *args, **options):
        to_email = options["to_email"]
        message = options["message"]
        subject = options["subject"]
        from_user = options.get("from_user")

        if not from_user and not SES_FROM_EMAIL:
            raise CommandError(
                "No sender configured. Provide --from-user or set SES_FROM_USER."
            )

        try:
            response = send_email_notification(
                to_email=to_email,
                subject=subject,
                body_text=message,
                from_user=from_user,
            )
        except Exception as exc:
            logger.error(
                "SES email send failed",
                to_email=to_email,
                from_user=from_user,
                error=str(exc),
            )
            raise CommandError(f"Failed to send SES email: {exc}") from exc

        message_id = response.get("MessageId", "unknown")
        logger.info(
            "SES email sent",
            to_email=to_email,
            from_user=from_user,
            message_id=message_id,
        )
        self.log(
            f"Sent SES email to {to_email}. MessageId: {message_id}",
            Levels.SUCCESS,
        )
