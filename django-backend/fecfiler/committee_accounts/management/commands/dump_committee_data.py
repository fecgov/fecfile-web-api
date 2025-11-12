from fecfiler.devops.management.commands.fecfile_base import FECCommand
from fecfiler.committee_accounts.utils.data import dump_committee_data
import structlog

logger = structlog.get_logger(__name__)


class Command(FECCommand):
    help = "Dump all data for a given committee into a valid JSON fixture"
    command_name = "dump_committee_data"

    def add_arguments(self, parser):
        parser.add_argument(
            "committee_id", help="The ID (not UUID) for the target committee"
        )
        parser.add_argument("--redis", action="store_true")

    def command(self, *args, **options):
        committee_id = options.get("committee_id")
        redis = options.get("redis", False)
        dump_committee_data(committee_id, redis)
