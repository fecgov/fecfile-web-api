# Generated by Django 5.0.8 on 2024-09-11 12:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web_services', '0002_uploadsubmission_task_completed_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadsubmission',
            name='fecfile_polling_attempts',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='webprintsubmission',
            name='fecfile_polling_attempts',
            field=models.IntegerField(default=0),
        ),
    ]
