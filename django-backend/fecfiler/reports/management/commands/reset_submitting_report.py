from fecfiler.devops.management.commands.fecfile_base import FECCommand
from ...utils.report import reset_submitting_report
import structlog

logger = structlog.get_logger(__name__)


class Command(FECCommand):
    help = "Reset all aspects of an in-progress report submission."
    command_name = "reset_submitting_report"

    def add_arguments(self, parser):
        parser.add_argument(
            "--report_id",
            type=str,
            required=True,
            help="The UUID of the report to reset.",
        )

    def command(self, *args, **options):
        report_id = options["report_id"]
        logger.info(
            f"""
                Beginning reset of the in-progress report submission with id {report_id}
                """
        )
        reset_submitting_report(report_id)
        logger.info(
            f"""
                Successfully reset the in-progress report submission with id {report_id}
                """
        )
