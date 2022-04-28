from django.db import migrations
from django.core.management import call_command


def forwards_func(apps, schema_editor):
    call_command(
        "loaddata",
        "fecfiler/f3x_summaries/fixtures/test_db_f3x_summaries.json",
    )


class Migration(migrations.Migration):

    dependencies = [
        ("f3x_summaries", "0006_alter_f3xsummary_committee_account"),
    ]

    operations = [
        migrations.RunPython(forwards_func),
    ]
