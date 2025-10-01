from fecfiler.devops.management.commands.fecfile_base import FECCommand
from ...utils.submission_utils import fail_open_submissions
import structlog

logger = structlog.get_logger(__name__)


class Command(FECCommand):
    help = "Set the state of all in-progress report submission tasks to FAILED."
    command_name = "fail_open_submissions"

    def command(self, *args, **options):
        logger.info(
            f"""
                Beginning fail of all in-progress report submissions.
                """
        )
        fail_open_submissions()
        logger.info(
            f"""
                Completed failing all in-progress report submissions.
                """
        )
