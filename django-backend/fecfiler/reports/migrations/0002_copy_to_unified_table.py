from django.db import migrations
from django.contrib.contenttypes import management
import copy
import uuid


def copy_f3x_summaries(apps, schema_editor):
    # update contenttype table to have reports entry
    app_config = apps.get_app_config("reports")
    if not hasattr(app_config, "models_module"):
        app_config.models_module = True
    management.create_contenttypes(app_config)
    if app_config.models_module is True:
        app_config.models_module = None

    try:
        F3XSummary = apps.get_model("f3x_summaries", "F3XSummary")  # noqa
        Report = apps.get_model("reports", "Report")  # noqa
        ReportF3X = apps.get_model("reports", "ReportF3X")  # noqa
        reports_to_copy = F3XSummary.objects.all()
        f3x_to_copy = copy.deepcopy(reports_to_copy)
        f3x_ids = []
        for f3x_report in f3x_to_copy:
            new_f3x_uuid = uuid.uuid4()
            f3x_ids.append(new_f3x_uuid)
            f3x_report.id = new_f3x_uuid
        ReportF3X.objects.bulk_create(f3x_to_copy)
        for index, report in enumerate(reports_to_copy):
            report.report_f3x_id = f3x_ids[index]
            report.report_f24_id = None
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
