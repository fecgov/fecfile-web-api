from django.db import migrations
from fecfiler.reports.models import Report


def test_data(apps, schema_editor):
    r = Report()
    r.objects.get()


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0008_remove_form1m_city_remove_form1m_committee_name_and_more"),
    ]

    operations = [
        migrations.RunPython(test_data),
    ]
