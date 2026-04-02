from fecfiler.devops.management.commands.fecfile_base import FECCommand
from fecfiler.committee_accounts.utils.accounts import enable_committee_account
import structlog

logger = structlog.get_logger(__name__)


class Command(FECCommand):
    help = "Enables a committee account"
    command_name = "enable_committee_account"

    def add_arguments(self, parser):
        parser.add_argument(
            "committee_id", type=str, help="The ID of the committee account to enable"
        )

    def command(self, *args, **options):
        committee_id = options["committee_id"]
        enable_committee_account(committee_id)
