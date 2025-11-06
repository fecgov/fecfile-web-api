from fecfiler.devops.management.commands.fecfile_base import FECCommand
from fecfiler.user.utils import disable_user


class Command(FECCommand):
    help = "Disable (or re-enable) a user with a given email."
    command_name = "disable_user"

    def add_arguments(self, parser):
        # require either a UUID or email
        id_arg = parser.add_mutually_exclusive_group(required=True)
        id_arg.add_argument(
            "--uuid", type=str, help="The UUID of the user to be disabled/enabled."
        )
        id_arg.add_argument(
            "--email",
            type=str,
            help="The email address of the user to be disabled/enabled.",
        )
        # add an --enable flag that defaults to false if not found
        parser.add_argument(
            "-e",
            "--enable",
            action="store_true",
            help="Flag to instead (re-)enable the user.",
        )

    def command(self, *args, **options):
        uuid = options["uuid"]
        email = options["email"]
        enable = options["enable"]
        disable_user(uuid, email, enable)
