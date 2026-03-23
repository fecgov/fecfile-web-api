# Manually squashed by Dan-go 48.0.12 on 2026-03-12 16:15

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    replaces = [
        ("memo_text", "0001_initial"),
        ("memo_text", "0002_initial"),
        ("memo_text", "0003_memotext_text_prefix")
    ]

    dependencies = [
        (
            "committee_accounts",
            "0001_squashed_0007_alter_committeeaccount_members",
        ),
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MemoText",
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
                ("rec_type", models.TextField(blank=True, null=True)),
                ("is_report_level_memo", models.BooleanField(default=True)),
                ("transaction_id_number", models.TextField(blank=True, null=True)),
                ("transaction_uuid", models.TextField(blank=True, null=True)),
                ("text4000", models.TextField(blank=True, null=True)),
                ("text_prefix", models.TextField(blank=True, null=True)),
                (
                    "committee_account",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="committee_accounts.committeeaccount",
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="reports.report",
                    ),
                ),
            ],
            options={
                "db_table": "memo_text",
            },
        ),
    ]
