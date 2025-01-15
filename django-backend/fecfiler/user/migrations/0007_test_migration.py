# Generated by Django 5.1.4 on 2025-01-15 18:35

from django.db import migrations
from time import sleep


def sleep_ten_minutes(apps, schema_editor):
    sleep(7.5*60)  # Sleeps for ten minutes
    return None


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0006_remove_old_login_accounts'),
    ]

    operations = [
        migrations.RunPython(
            sleep_ten_minutes,
            migrations.RunPython.noop,
        ),
    ]
