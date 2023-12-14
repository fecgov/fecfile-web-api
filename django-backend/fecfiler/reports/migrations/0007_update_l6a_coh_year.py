from django.db import migrations


def update_coh_year(apps, schema_editor):
    Report = apps.get_model("reports", "Report")  # noqa
    reports_to_update = Report.objects.filter(
        form_3x__isnull=False,
        coverage_from_date__isnull=False
    )
    for report in reports_to_update:
        year = report.coverage_from_date.year
        report.form_3x.L6a_year_for_above_ytd = year
        report.form_3x.save()


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("reports", "0006_report_calculation_token"),
    ]

    operations = [
        migrations.RunPython(update_coh_year, migrations.RunPython.noop),
    ]
