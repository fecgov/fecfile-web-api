from django.db import migrations
from django.contrib.contenttypes import management


def copy_scha_transactions(apps, schema_editor):
    # update contenttype table to have scheduleatransaction entry
    app_config = apps.get_app_config("transactions")
    if not hasattr(app_config, "models_module"):
        app_config.models_module = True
    management.create_contenttypes(app_config)
    if app_config.models_module is True:
        app_config.models_module = None

    try:
        Transaction = apps.get_model("transactions", "Transaction")  # noqa
        ScheduleA = apps.get_model("transactions", "ScheduleA")  # noqa
        ScheduleATransaction = apps.get_model(  # noqa
            "transactions", "ScheduleATransaction"
        )
        transactions_to_copy = ScheduleATransaction.objects.all()
        for transaction in transactions_to_copy:
            print(f"AHOY {transaction}")
            schedule_a = ScheduleA(transaction)
            schedule_a.save()
            transaction.schedule_a = schedule_a
            transaction.schedule_a_id = schedule_a.id
        Transaction.objects.bulk_create(transactions_to_copy)
    except LookupError:
        print("No ScheduleATransaction table to copy")


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("transactions", "0003_schedulea_transaction"),
    ]

    operations = [
        migrations.RunPython(copy_scha_transactions, migrations.RunPython.noop),
    ]
