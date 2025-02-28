# Generated by Django 5.1.5 on 2025-02-25 00:18

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("committee_accounts", "0006_alter_membership_committee_account_and_more"),
        ("transactions", "0015_merge_transaction_triggers"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScheduleF",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "filer_designated_to_make_coordianted_expenditures",
                    models.BooleanField(blank=True, null=True),
                ),
                ("designating_committee_name", models.TextField(blank=True)),
                ("expenditure_date", models.DateField(blank=True, null=True)),
                (
                    "expenditure_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "aggregate_general_elec_expended",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                ("expenditure_purpose_descrip", models.TextField(blank=True)),
                ("category_code", models.TextField(blank=True)),
                ("memo_text_description", models.TextField(blank=True)),
                (
                    "designating_committee_account",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="committee_accounts.committeeaccount",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="transaction",
            name="schedule_f",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="transactions.schedulef",
            ),
        ),
    ]
