from django.db import migrations
from django.contrib.contenttypes import management


def copy_f3x_summaries(apps, schema_editor):
    # update contenttype table to have reports entry
    app_config = apps.get_app_config("reports")
    if not hasattr(app_config, "models_module"):
        app_config.models_module = True
    management.create_contenttypes(app_config)
    if app_config.models_module is True:
        app_config.models_module = None

    try:
        Report = apps.get_model("reports", "Report")
        Form3X = apps.get_model("reports", "Form3X")  # noqa
        F3XSummary = apps.get_model("f3x_summaries", "F3XSummary")  # noqa
        reports_to_copy = F3XSummary.objects.all()
        for report in reports_to_copy:
            report.form_3x_id = report.id
            report.form_24_id = None
        Form3X.objects.bulk_create(reports_to_copy)
        Report.objects.bulk_create(reports_to_copy)
    except Exception as e:
        print("Failed to copy f3x_summaries table due to: " + str(e))


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(copy_f3x_summaries, migrations.RunPython.noop),
    ]
