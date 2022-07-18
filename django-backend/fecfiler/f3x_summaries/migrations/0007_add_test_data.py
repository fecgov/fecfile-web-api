from django.db import migrations
from django.core import serializers
from django.core.management import call_command
##from apps.common.utils import loaddata


"""def forwards_func(apps, schema_editor):
    ##SchATransaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa
    apps.common.utils.loaddata(schema_editor, "fecfiler/f3x_summaries/fixtures/test_db_f3x_summaries.json")
    ##call_command(
    ##    "loaddata",
    ##    "fecfiler/f3x_summaries/fixtures/test_db_f3x_summaries.json",
    ##)"""

def forwards_func(apps, schema_editor):
    original_apps = serializers.python.apps
    serializers.python.apps = apps
    fixture_file = 'fecfiler/f3x_summaries/fixtures/test_db_f3x_summaries.json'
    fixture = open(fixture_file)
    objects = serializers.deserialize('json', fixture, ignorenonexistent=True)
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
