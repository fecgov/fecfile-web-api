from django.core.management.base import BaseCommand
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.views import create_committee_view


class Command(BaseCommand):
    help = "Create or update committee views"

    def handle(self, *args, **options):
        for committee in CommitteeAccount.objects.all():
            create_committee_view(committee.id)

        self.stdout.write(self.style.SUCCESS("Successfully created/updated committee views"))
