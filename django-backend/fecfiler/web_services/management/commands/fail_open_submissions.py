from fecfiler.devops.management.commands.fecfile_base import FECCommand
from ...utils.submission import fail_open_submissions
import structlog

logger = structlog.get_logger(__name__)


class Command(FECCommand):
    help = "Set the state of all in-progress report submission tasks to FAILED."
    command_name = "fail_open_submissions"

    def command(self, *args, **options):
        logger.info("Start: fail all in-progress report submissions.")
        fail_open_submissions()
        logger.info("Completed: fail all in-progress report submissions.")
