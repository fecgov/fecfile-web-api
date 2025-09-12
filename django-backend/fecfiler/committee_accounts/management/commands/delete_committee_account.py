from django.core.management.base import BaseCommand
from fecfiler.committee_accounts.models import CommitteeAccount
import structlog

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Deletes a committee account"

    def add_arguments(self, parser):
        parser.add_argument(
            "committee_id", type=str, help="The ID of the committee account to delete"
        )

    def handle(self, *args, **options):
        committee_id = options["committee_id"]
        try:
            committee_account = CommitteeAccount.objects.filter(
                committee_id=committee_id
            ).first()
            if committee_account is None:
                logger.error(f"Committee account with ID {committee_id} does not exist.")
                return
            # because of how we've set up our cascade deletes, deleting the account
            # will also delete all associated reports, transactions and contacts
            committee_account.hard_delete()
            logger.info(f"Committee account with ID {committee_id} has been deleted.")
        except Exception as e:
            logger.error(f"An error occurred while deleting the committee account: {e}")
