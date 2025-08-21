from fecfiler.devops.management.commands.fecfile_base import FECCommand
from fecfiler.committee_accounts.committee_membership_utils import add_user_to_committee
from fecfiler.committee_accounts.models import Membership
import structlog

logger = structlog.get_logger(__name__)


class Command(FECCommand):
    help = "Adds a user to a committee account"
    command_name = "add_user_to_committee"

    def add_arguments(self, parser):
        parser.add_argument("user_email", type=str)
        parser.add_argument("committee_id", type=str)

    def command(self, *args, **options):
        try:
            user_email = options["user_email"]
            committee_id = options["committee_id"]
            logger.info(
                f"""
                [Account Override] Adding user_email {user_email}
                to committee {committee_id}
                """
            )
            add_user_to_committee(
                user_email,
                committee_id,
                Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
            )
            logger.info(
                f"""
                [Account Override] Successfully added user_email {user_email}
                to committee {committee_id}"
                """
            )
        except Exception as e:
            logger.error(
                f"""
                [Account Override] Failed to add user_email {user_email}
                to committee {committee_id} due to Exception {str(e)}
                """
            )
            raise e
