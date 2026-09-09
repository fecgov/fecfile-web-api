from django.db import migrations


class Migration(migrations.Migration):

    def clear_aggregates_for_null_groups(apps, schema_editor):
        transaction = apps.get_model("transactions", "Transaction")
        transaction.objects.filter(aggregation_group__isnull=True).update(
            aggregate=None, _calendar_ytd_per_election_office=None
        )

    dependencies = [
        ("transactions", "0003_remove_unused_functions"),
    ]

    operations = [
        migrations.RunPython(
            clear_aggregates_for_null_groups,
        ),
    ]
