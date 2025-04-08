from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0019_aggregate_committee_controls"),
    ]

    def trigger_save_on_transactions(apps, schema_editor):
        transactions = apps.get_model("transactions", "transaction")
        transactions.objects.update(id=models.F('id'))

    operations = [
        migrations.RunPython(trigger_save_on_transactions, migrations.RunPython.noop),
    ]
