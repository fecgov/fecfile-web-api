from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from fecfiler.committee_accounts.models import CommitteeAccount, Membership
import structlog

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Add a user to a committee account. If the user does not exist, set pending membership."

    def add_arguments(self, parser):
        # require either ID or UUID
        committee_arg = parser.add_mutually_exclusive_group(required=True)
        committee_arg.add_argument(
            "--uuid",
            type=str,
            help="The UUID of the committee account to which to add the user",
        )
        committee_arg.add_argument(
            "--id",
            type=str,
            help="The ID of the committee account to which to add the user",
        )
        parser.add_argument(
            "-u",
            "--user",
            type=str,
            required=True,
            help="The email address of the user to be added",
        )

    def handle(self, *args, **options):
        # Find committee account by UUID or ID
        if options["uuid"]:
            committee_account = CommitteeAccount.objects.filter(
                id=options["uuid"]
            ).first()
            committee_arg = f"UUID {options['uuid']}"
        else:
            committee_account = CommitteeAccount.objects.filter(
                committee_id=options["id"]
            ).first()
            committee_arg = f"ID {options['id']}"

        if committee_account is None:
            raise CommandError(f"Committee account with {committee_arg} does not exist.")

        user_email = options["user"]
        user_model = get_user_model()
        user = user_model.objects.get(email=user_email)
        if user:
            # Add user to committee account (create membership if not exists)
            membership, created = Membership.objects.get_or_create(
                committee_account=committee_account,
                user=user,
                defaults={
                    "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
                },
            )
            if created:
                output = f"User {user_email} added to committee account {committee_account.committee_id}."
                logger.info(output)
                self.stdout.write(self.style.SUCCESS(output))
            else:
                output = f"User {user_email} is already a member of committee account {committee_account.committee_id}."
                logger.info(output)
                self.stdout.write(self.style.WARNING(output))
        else:
            # Create pending membership for non-existent user
            membership, created = Membership.objects.get_or_create(
                committee_account=committee_account,
                pending_email=user_email,
                defaults={
                    "role": Membership.CommitteeRole.COMMITTEE_ADMINISTRATOR,
                },
            )
            output = f"Pending membership created for {user_email} in committee account {committee_account.committee_id}."
            logger.info(output)
            self.stdout.write(self.style.SUCCESS(output))
