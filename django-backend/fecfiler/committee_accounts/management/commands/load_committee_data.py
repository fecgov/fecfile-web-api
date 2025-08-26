from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from fecfiler.user.utils import get_user_by_email_or_id
import json
import structlog

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Loads committee data from a json file and adds a given user to the newly created committee"

    def add_arguments(self, parser):
        parser.add_argument(
            "filename", type=str, help="The json file containing the committee data to be loaded"
        )
        parser.add_argument(
            "user_identifier",
            help="The email or UUID of the user to add to the new committee"
        )

    def get_committee_id_from_file(self, filename) -> str | None:
        file = open(filename, "r")
        data = json.load(file)
        for data_model in data:
            if data_model["model"] == "committee_accounts.committeeaccount":
                return data_model["fields"]["committee_id"]

    def handle(self, *args, **options):
        user_identifier = options.get("user_identifier", "")
        user = get_user_by_email_or_id(user_identifier)
        if user is None:
            raise CommandError("No matching user found")

        filename = options.get("filename")
        committee_id = self.get_committee_id_from_file(filename)

        try:
            logger.info(f"Loading data for committee {committee_id}")
            call_command("loaddata", options.get("filename"))
            logger.info(f"Adding user {user.email} to new committee {committee_id}")
            call_command("add_user_to_committee", user.email, committee_id)
        except Exception as e:
            logger.error(f"An error occurred while deleting the committee account: {e}")