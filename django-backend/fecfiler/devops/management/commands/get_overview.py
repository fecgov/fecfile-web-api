from fecfiler.devops.management.commands.fecfile_base import FECCommand
from ...utils.common_queries import (
    get_num_committees,
    get_num_users,
    get_num_reports,
    get_num_reports_per_committee,
    get_num_transactions_per_committee,
    get_num_transactions_per_report,
    get_num_transactions_per_contact,
    get_transaction_types_breakdown,
    get_transaction_tiers_breakdown,
    get_carryover_type_transactions,
)
import structlog

logger = structlog.get_logger(__name__)


class Command(FECCommand):
    help = "Get an overview with various statistics."
    command_name = "get_overview"

    def add_arguments(self, parser):
        parser.add_argument(
            "--committee_id",
            type=str,
            required=False,
            default=None,
            help="Committee by which to filter.",
        )

    def command(self, *args, **options):
        committee_id = options["committee_id"]
        logger.info(
            f"Beginning overview generation"
            f"{f' with committee_id {committee_id}' if committee_id is not None else ''}"
        )

        if not committee_id:
            get_num_committees()
            get_num_users()
            get_num_reports()

        get_num_reports_per_committee(committee_id)
        get_num_transactions_per_committee(committee_id)
        get_num_transactions_per_report(committee_id)

        if not committee_id:
            get_num_transactions_per_contact()
            get_transaction_types_breakdown()
            get_transaction_tiers_breakdown()
            get_carryover_type_transactions()

        logger.info(
            f"Successfully generated overview"
            f"{f' with committee_id {committee_id}' if committee_id is not None else ''}"
        )
