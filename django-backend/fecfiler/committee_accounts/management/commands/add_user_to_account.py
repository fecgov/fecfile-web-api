from fecfiler.devops.management.commands.fecfile_base import FECCommand
from fecfiler.committee_accounts.committee_membership_utils import add_user_to_committee
from fecfiler.committee_accounts.models import Membership


class Command(FECCommand):
    help = "Generate Locust load test data"
    command_name = "gen_locust_load_test_data"

    def add_arguments(self, parser):
        parser.add_argument("user_email", type=str)
        parser.add_argument("committee_id", type=str)

    def command(self, *args, **options):
        add_user_to_committee(
            options["user_email"],
            options["committee_id"],
            Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
        )
