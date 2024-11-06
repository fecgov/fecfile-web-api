from django.core.management.base import BaseCommand
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.utils import create_committee_view


class Command(BaseCommand):
    help = "Create or update committee views"

    def handle(self, *args, **options):
        for committee in CommitteeAccount.objects.all():
            self.stdout.write(
                self.style.NOTICE(f"Running create_committee_view on {committee.id}")
            )
            create_committee_view(committee.id)

        self.stdout.write(
            self.style.SUCCESS("Successfully created/updated committee views")
        )
