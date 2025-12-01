from fecfiler.devops.management.commands.fecfile_base import FECCommand
from fecfiler.user.utils import reset_security_consent_date


class Command(FECCommand):
    help = """Resets the security consent expiration date
    for the user corresponding to the given email"""
    command_name = "reset_security_consent_date"

    def add_arguments(self, parser):
        parser.add_argument(
            "email",
            type=str,
            help="""The email of the user account
            whose security consent date will be reset""",
        )

    def command(self, *args, **options):
        email = options["email"]
        reset_security_consent_date(email)
