from fecfiler.devops.management.commands.fecfile_base import FECCommand
from fecfiler.committee_accounts.utils.data import (
    load_mocked_committee_data,
)
import structlog

logger = structlog.get_logger(__name__)


class Command(FECCommand):
    help = "Load mock committee data into redis"
    command_name = "load_mocked_committee_data"

    def add_arguments(self, parser):
        parser.add_argument("--s3", action="store_true")

    def command(self, *args, **options):
        s3 = options.get("s3", False)
        load_mocked_committee_data(s3)
