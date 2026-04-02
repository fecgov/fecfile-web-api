from .fecfile_base import FECCommand
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.utils.accounts import (
    disable_committee_account,
    logout_committee_sessions,
)
import structlog

logger = structlog.get_logger(__name__)


class Command(FECCommand):
    help = "Disables a committee account"
    command_name = "disable_committee_account"

    def add_arguments(self, parser):
        parser.add_argument("committee_id", type=str)

    def command(self, *args, **options):
        try:
            committee_id = options["committee_id"]
            logger.info(f"Disabling committee {committee_id}")
            disable_committee_account(committee_id)
            logout_committee_sessions(committee_id)

        except CommitteeAccount.DoesNotExist:
            logger.error(f"Committee account with ID {committee_id} does not exist.")
        except Exception as e:
            logger.error(f"Error occurred while disabling committee {committee_id}: {e}")
            raise
