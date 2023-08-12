# Generated by Django 3.2.12 on 2022-09-16 13:04

from django.db import migrations


def clean_dotfec(apps, schema_editor):
    DotFEC = apps.get_model("web_services", "DotFEC")  # noqa
    DotFEC.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("web_services", "0015_alter_dotfec_report_step_1"),
    ]

    operations = [
        migrations.RunPython(clean_dotfec),
    ]