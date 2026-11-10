from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from import_export_extensions.models import ImportJob

from fecfiler.contacts.imports.resource import ContactImportResource


class Command(BaseCommand):
    help = "Preview cleanup of old contact-import jobs and files; --delete applies it."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7)
        parser.add_argument("--delete", action="store_true")

    def handle(self, *args, **options):
        if options["days"] < 1:
            raise CommandError("--days must be at least 1")
        jobs = ImportJob.objects.filter(
            resource_path=ContactImportResource.class_path,
            modified__lt=timezone.now() - timedelta(days=options["days"]),
            import_status__in=[
                "PARSED",
                "INPUT_ERROR",
                "PARSE_ERROR",
                "IMPORTED",
                "IMPORT_ERROR",
                "CANCELLED",
            ],
        )
        if not options["delete"]:
            self.stdout.write(
                f"Would delete {jobs.count()} old contact-import jobs and their files."
            )
            return
        count = 0
        with transaction.atomic():
            for job in jobs.select_for_update(skip_locked=True).iterator():
                # Active jobs are excluded; delete only files owned by this job.
                job.data_file.delete(save=False)
                if job.input_errors_file:
                    job.input_errors_file.delete(save=False)
                job.delete()
                count += 1
        self.stdout.write(f"Deleted {count} old contact-import jobs and their files.")
