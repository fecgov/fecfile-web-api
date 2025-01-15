# Generated by Django 5.1.4 on 2025-01-15 18:35

from django.db import migrations
from time import sleep


def sleep_ten_seconds(apps, schema_editor):
    sleep(10)  # Sleeps for ten seconds
    return None


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0007_test_migration'),
    ]

    operations = [
        migrations.RunPython(
            sleep_ten_seconds,
            migrations.RunPython.noop,
        ),
    ]
