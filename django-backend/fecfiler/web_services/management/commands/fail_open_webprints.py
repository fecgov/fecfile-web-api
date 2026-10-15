from fecfiler.devops.management.commands.fecfile_base import FECCommand
from ...utils.submission import fail_open_webprints
import structlog

logger = structlog.get_logger(__name__)


class Command(FECCommand):
    help = "Set the state of all in-progress report web print tasks to FAILED."
    command_name = "fail_open_webprints"

    def command(self, *args, **options):
        logger.info("Start: fail all in-progress report web print tasks.")
        fail_open_webprints()
        logger.info("Completed: fail all in-progress report web print tasks.")
