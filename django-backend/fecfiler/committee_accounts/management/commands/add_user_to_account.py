from django.core.management.base import BaseCommand
from git import CommandError
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.user.models import User
import structlog

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Adds a user to a committee account"

    def add_arguments(self, parser):
        # require either a UUID of committee account or FEC ID of committee
        committee_argument = parser.add_mutually_exclusive_group(required=True)
        committee_argument.add_argument(
            "--committee_uuid",
            type=str,
            help="The UUID of the committee to add the user to.",
        )
        committee_argument.add_argument(
            "--committee_fec_id",
            type=str,
            help="The FEC ID of the committee to add the user to.",
        )
        # require either UUID or email of user
        user_argument = parser.add_mutually_exclusive_group(required=True)
        user_argument.add_argument(
            "--user_uuid", type=str, help="The UUID of the user to add to the committee."
        )
        user_argument.add_argument(
            "--user_email",
            type=str,
            help="The email address of the user to add to the committee.",
        )

    def handle(self, *args, **options):
        try:
            """
            Get the committee account based on the provided UUID or FEC ID.
            """
            committee_account_uuid = options["committee_uuid"]
            if committee_account_uuid:
                committee_account = self.get_committee_account_by_uuid(
                    committee_account_uuid
                )
                if not committee_account:
                    raise CommandError(
                        f"Committee account with UUID {committee_account_uuid} does not exist."
                    )
            else:
                committee_fec_id = options["committee_fec_id"]
                committee_account = CommitteeAccount.objects.filter(
                    committee_id=committee_fec_id
                ).first()
                if not committee_account:
                    raise CommandError(
                        f"Committee account with FEC ID {committee_fec_id} does not exist."
                    )
        except Exception as e:
            raise CommandError(
                f"An error occurred while retrieving the committee account: {e}"
            )

        try:
            """
            Get the user based on the provided UUID or email.
            """
            user_uuid = options["user_uuid"]
            if user_uuid:
                user = User.objects.filter(id=user_uuid).first()
                if not user:
                    raise CommandError(f"User with UUID {user_uuid} does not exist.")
            else:
                user_email = options["user_email"]
                user = User.objects.filter(email=user_email).first()
                if not user:
                    raise CommandError(f"User with email {user_email} does not exist.")
        except Exception as e:
            raise CommandError(f"An error occurred while retrieving the user: {e}")

        try:
            """
            Add the user to the committee account.
            """
            self.stdout.write(
                self.style.SUCCESS(
                    f"User [{user.id} | {user.email}] has been added to committee account [{committee_account.id} | {committee_account.committee_id}]."
                )
            )

            logger.info(
                f"User with ID {user.id} has been added to committee account with ID {committee_account.id}."
            )
        except Exception as e:
            logger.error(
                f"An error occurred while adding the user to the committee account: {e}"
            )
