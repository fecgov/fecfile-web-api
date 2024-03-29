# Generated by Django 4.2.7 on 2024-01-16 20:15

import django.core.validators
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CommitteeAccount",
            fields=[
                ("deleted", models.DateTimeField(blank=True, null=True)),
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
                    "committee_id",
                    models.CharField(
                        max_length=9,
                        unique=True,
                        validators=[
                            django.core.validators.RegexValidator(
                                "^C[0-9]{8}$", "invalid committee id format"
                            )
                        ],
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "committee_accounts",
            },
        ),
    ]
