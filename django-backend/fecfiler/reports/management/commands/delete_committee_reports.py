from django.core.management.base import BaseCommand
from fecfiler.reports.utils.report_utils import delete_committee_reports
import structlog

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Delete all reports (and transactions) for a given committee"
    command_name = "delete_committee_reports"

    def add_arguments(self, parser):
        parser.add_argument("committee_id", nargs=1, type=str)
        parser.add_argument(
            "--delete-contacts",
            action="store_true",
            help="Also delete contacts associated with the committee",
        )

    def command(self, *args, **options):
        committee_id = options.get("committee_id", None)
        delete_contacts = options.get("delete_contacts", False)
        delete_committee_reports(committee_id, delete_contacts)
