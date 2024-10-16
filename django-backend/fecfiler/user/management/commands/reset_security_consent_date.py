from django.core.management.base import BaseCommand
from fecfiler.user.models import User
import structlog

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = """Resets the security consent expiration date
    for the user corresponding to the given email"""

    def add_arguments(self, parser):
        parser.add_argument(
            "email",
            type=str,
            help="""The email of the user account
            whose security consent date will be reset"""
        )

    def handle(self, *args, **options):
        email = options["email"]
        try:
            user = User.objects.filter(email=email).first()
            if user is None:
                logger.error("No user found matching that email")

            user.security_consent_exp_date = None
            user.save()

            logger.info("Successfully reset the security consent expiration date")
        except Exception as e:
            logger.error(
                f"An error occurred while reseting the security consent date: {e}"
            )
