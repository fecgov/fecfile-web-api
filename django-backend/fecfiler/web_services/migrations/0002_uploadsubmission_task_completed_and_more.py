# Generated by Django 5.0.8 on 2024-08-22 19:42

from django.db import migrations, models
from django.db.models import F


def set_default_task_completed_times(apps, schema_editor):
    uploads = apps.get_model("web_services", "UploadSubmission")
    web_prints = apps.get_model("web_services", "WebPrintSubmission")

    uploads.objects.all().update(task_completed=F("updated"))
    web_prints.objects.all().update(task_completed=F("updated"))


class Migration(migrations.Migration):

    dependencies = [
        ('web_services', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadsubmission',
            name='task_completed',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='webprintsubmission',
            name='task_completed',
            field=models.DateTimeField(null=True),
        ),
        migrations.RunPython(set_default_task_completed_times, migrations.RunPython.noop)
    ]
