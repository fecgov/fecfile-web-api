from django.core.management.base import BaseCommand, CommandError
from fecfiler.reports.models import Report

# from summary.tasks import CalculationState


class Command(BaseCommand):
    help = "Reset state of summary calculation."

    def add_arguments(self, parser):
        parser.add_argument(
            "uuid",
            type=str,
            help="The ID of the report for which to reset the summary calculation.",
        )

    def handle(self, *args, **options):
        try:
            report = Report.objects.get(id=options["uuid"])
        except Report.DoesNotExist:
            raise CommandError("Report ID does not exist")

        report.calculation_status = ""  # CalculationState.CALCULATING
        report.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"The calculation_status for report {options['uuid']} has been reset."
            )
        )
