from django.db import migrations, models
from django.contrib.postgres.fields import ArrayField


def update_blocking_reports_default(apps, schema_editor):
    transaction = apps.get_model("transactions", "Transaction")
    transaction._meta.get_field("blocking_reports").default = list


class Migration(migrations.Migration):
    dependencies = [
        ("transactions", "0011_transaction_can_delete"),
    ]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="blocking_reports",
            field=ArrayField(
                base_field=models.UUIDField(),
                blank=False,
                default=list,
                size=None,
            ),
        ),
        migrations.RunPython(update_blocking_reports_default),
    ]
