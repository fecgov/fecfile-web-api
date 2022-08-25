# Generated by Django 3.2.12 on 2022-08-08 15:22

from django.db import migrations


def patch_report_code_label(apps, schema_editor):
    report_code_label_model = apps.get_model("f3x_summaries", "ReportCodeLabel")  # noqa
    errant_object = report_code_label_model.objects.get(report_code="MY")
    errant_object.label = "JULY 31 (MY)"
    errant_object.save()


class Migration(migrations.Migration):

    dependencies = [
        ('f3x_summaries', '0013_auto_20220807_0743'),
    ]

    operations = [
        migrations.RunPython(
            code=patch_report_code_label,
            reverse_code=migrations.RunPython.noop
        )
    ]
