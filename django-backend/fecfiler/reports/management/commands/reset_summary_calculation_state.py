from fecfiler.devops.management.commands.fecfile_base import FECCommand
from ...utils.report_utils import reset_summary_calculation_state
import structlog

logger = structlog.get_logger(__name__)


class Command(FECCommand):
    help = "Reset Summary Calculation State"
    command_name = "reset_summary_calculation_state"

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
                Begining reset of the calculation status of report with id {report_id}
                """
        )
        reset_summary_calculation_state(report_id)
        logger.info(
            f"""
                Successfully reset the calculation status of report with id {report_id}
                """
        )
