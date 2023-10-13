# Generated by Django 4.1.3 on 2023-10-13 17:41

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0002_copy_to_unified_table"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportF99",
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
                ("street_1", models.TextField(blank=True, null=True)),
                ("street_2", models.TextField(blank=True, null=True)),
                ("city", models.TextField(blank=True, null=True)),
                ("state", models.TextField(blank=True, null=True)),
                ("zip", models.TextField(blank=True, null=True)),
                ("text_code", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.AddField(
            model_name="report",
            name="report_f99",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="reports.reportf99",
            ),
        ),
    ]
