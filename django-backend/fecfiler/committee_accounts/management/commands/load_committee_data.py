from fecfiler.devops.management.commands.fecfile_base import FECCommand
from fecfiler.committee_accounts.utils.data import (
    load_committee_data,
)
import structlog

logger = structlog.get_logger(__name__)


class Command(FECCommand):
    help = "Loads committee data from a json file and adds a given user as a member"
    command_name = "load_committee_data"

    def add_arguments(self, parser):
        parser.add_argument(
            "filename",
            type=str,
            help="The json file containing the committee data to be loaded"
        )
        parser.add_argument(
            "user_identifier",
            help="The email or UUID of the user to add to the new committee"
        )

    def command(self, *args, **options):
        user_identifier = options.get("user_identifier", "")
        filename = options.get("filename")
        load_committee_data(user_identifier, filename)
