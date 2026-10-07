from django.db import migrations
from fecfiler.transactions.models import Transaction
from fecfiler.transactions.managers import TransactionManager


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0008_remove_s_from_refund_type"),
    ]

    def recalculate_entity_aggregates(apps, schema_editor):
        trn_to_update = Transaction.objects.filter(
            force_unaggregated=True,
        )

        for idx, transaction in enumerate(trn_to_update):
            if transaction:
                print(f"""=== Processing transaction {idx + 1}/{trn_to_update.count()}
                     for committee {transaction.committee_account} ===""")
                print(
                    "retrieving transaction chain start for transaction:"
                    + str(transaction.id)
                )
                chain_start_transaction = (
                    Transaction.objects.annotate(date=TransactionManager.DATE_CLAUSE)
                    .filter(
                        contact_1=transaction.contact_1,
                        committee_account=transaction.committee_account,
                        aggregation_group=transaction.aggregation_group,
                    )
                    .order_by("date", "created")
                    .first()
                )
                if chain_start_transaction:
                    print(
                        "Saving first transaction in chain: ",
                        chain_start_transaction.id,
                    )
                    chain_start_transaction.save()
                    print("First transaction saved")
                else:
                    print(
                        "No chain start transaction found for transaction:",
                        transaction.id,
                    )

    operations = [
        migrations.RunPython(recalculate_entity_aggregates, migrations.RunPython.noop),
    ]
