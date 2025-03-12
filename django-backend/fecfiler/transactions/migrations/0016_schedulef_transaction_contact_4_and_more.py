# Generated by Django 5.1.5 on 2025-03-06 01:56

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0001_initial"),
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
            ],
        ),
        migrations.AddField(
            model_name="transaction",
            name="contact_4",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="contact_4_transaction_set",
                to="contacts.contact",
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="contact_5",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="contact_5_transaction_set",
                to="contacts.contact",
            ),
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
