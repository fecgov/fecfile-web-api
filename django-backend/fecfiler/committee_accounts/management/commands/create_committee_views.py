from django.core.management.base import BaseCommand
from fecfiler.committee_accounts.models import CommitteeAccount
from fecfiler.committee_accounts.utils import create_committee_view

import structlog


logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = "Create or update committee views"

    def handle(self, *args, **options):
        for committee in CommitteeAccount.objects.all():
            logger.info(f"Running create_committee_view on {committee.id}")
            create_committee_view(committee.id)

        logger.info("Successfully created/updated committee views")
