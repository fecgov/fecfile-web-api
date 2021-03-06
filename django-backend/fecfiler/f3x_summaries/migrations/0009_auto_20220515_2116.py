# Generated by Django 3.2.12 on 2022-05-16 01:16

from django.db import migrations, models


def convert_fecfile_booleans(apps, schema_editor):
    retrieved_f3x_summary_class = apps.get_model("f3x_summaries", "F3XSummary")  # noqa

    for f3x_summary in retrieved_f3x_summary_class.objects.all():
        f3x_summary.change_of_address = (
            True if f3x_summary.change_of_address in ["true", "X"] else False
        )
        f3x_summary.qualified_committee = (
            True if f3x_summary.qualified_committee in ["true", "X"] else False
        )
        f3x_summary.save()


class Migration(migrations.Migration):

    dependencies = [
        ("f3x_summaries", "0008_auto_20220503_1411"),
    ]

    operations = [
        migrations.RunPython(convert_fecfile_booleans),
        migrations.AlterField(
            model_name="f3xsummary",
            name="change_of_address",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
        migrations.AlterField(
            model_name="f3xsummary",
            name="qualified_committee",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
