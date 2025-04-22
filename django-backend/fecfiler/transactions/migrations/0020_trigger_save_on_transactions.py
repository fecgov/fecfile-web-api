from django.db import migrations
import structlog

logger = structlog.get_logger(__name__)


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0019_aggregate_committee_controls"),
    ]

    def trigger_save_on_transactions(apps, schema_editor):
        transactions = apps.get_model("transactions", "transaction")
        committees = apps.get_model("committee_accounts", "committeeaccount")
        contacts = apps.get_model("contacts", "contact")

        # Update transactions for each committee
        for committee in committees.objects.all():
            logger.info(f"Committee:{committee.committee_id}")

            # For each contact, update the first schedule A transaction
            for contact in contacts.objects.filter(committee_account=committee):
                logger.info(f"Contact: {contact}")
                first_schedule_a = (
                    transactions.objects.filter(
                        schedule_a__isnull=False,
                        contact_1=contact,
                        committee_account=committee,
                    )
                    .order_by("schedule_a__contribution_date", "created")
                    .first()
                )
                logger.info(f"First Schedule A: {first_schedule_a}")
                if first_schedule_a:
                    logger.info(f"Saving first schedule A")
                    first_schedule_a.save()

            # Election Aggregates
            elections = transactions.objects.filter(
                schedule_e__isnull=False,
                committee_account=committee,
            ).values(
                "contact_2__candidate_office",
                "contact_2__candidate_state",
                "contact_2__candidate_district",
                "schedule_e__election_code",
            )
            for election in elections:
                logger.info(f"Election: {election}")
                first_schedule_e = (
                    transactions.objects.filter(
                        schedule_e__isnull=False,
                        contact_2__candidate_office=election[
                            "contact_2__candidate_office"
                        ],
                        contact_2__candidate_state=election["contact_2__candidate_state"],
                        contact_2__candidate_district=election[
                            "contact_2__candidate_district"
                        ],
                        schedule_e__election_code=election["schedule_e__election_code"],
                        committee_account=committee,
                    )
                    .order_by(
                        "schedule_e__disbursement_date",
                        "created",
                    )
                    .first()
                )
                logger.info(f"First Schedule E: {first_schedule_e}")
                if first_schedule_e:
                    logger.info(f"Saving first schedule E")
                    first_schedule_e.save()

    operations = [
        migrations.RunPython(trigger_save_on_transactions, migrations.RunPython.noop),
    ]
