from django.db import migrations
from django.core import serializers
from django.core.management import call_command


def forwards_func(apps, schema_editor):
    original_apps = serializers.python.apps
    serializers.python.apps = apps
    fixture_file = 'fecfiler/f3x_summaries/fixtures/test_db_f3x_summaries.json'
    fixture = open(fixture_file)
    objects = serializers.deserialize('json', fixture)
    for obj in objects:
        obj.save()
    fixture.close()
    serializers.python.apps = original_apps


class Migration(migrations.Migration):

    dependencies = [
        ("f3x_summaries", "0006_alter_f3xsummary_committee_account"),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
