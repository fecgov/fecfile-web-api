from django.db import migrations
from django.db.models.functions import Coalesce
from fecfiler.transactions.aggregation import process_aggregation_for_election


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0010_transaction_entity_election_cycle_to_date"),
    ]

    def recalculate_election_aggregates(apps, schema_editor):
        DATE_CLAUSE = Coalesce(
            "schedule_e__disbursement_date",
            "schedule_e__dissemination_date",
        )
        transaction_model = apps.get_model("transactions", "Transaction")
        trn_to_update = transaction_model.objects.filter(
            schedule_e_id__isnull=False,
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
                    transaction_model.objects.annotate(date=DATE_CLAUSE)
                    .filter(
                        schedule_e__election_code=transaction.schedule_e.election_code,
                        contact_2__candidate_office=(
                            transaction.contact_2.candidate_office
                        ),
                        contact_2__candidate_state=(
                            transaction.contact_2.candidate_state
                        ),
                        contact_2__candidate_district=(
                            transaction.contact_2.candidate_district
                        ),
                        committee_account=transaction.committee_account,
                        aggregation_group=transaction.aggregation_group,
                    )
                    .order_by("date", "created")
                    .first()
                )
                if chain_start_transaction:
                    print(
                        "process_aggregation_for_election first transaction in chain: ",
                        chain_start_transaction.id,
                    )
                    process_aggregation_for_election(chain_start_transaction)
                    print("First transaction processed")
                else:
                    print(
                        "No chain start transaction found for transaction:",
                        transaction.id,
                    )

    operations = [
        migrations.RunPython(recalculate_election_aggregates, migrations.RunPython.noop),
    ]
