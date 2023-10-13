# Generated by Django 4.1.3 on 2023-10-09 21:34

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReportF24",
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
                ("report_type_24_48", models.TextField(blank=True, null=True)),
                ("original_amendment_date", models.DateField(blank=True, null=True)),
                ("street_1", models.TextField(blank=True, null=True)),
                ("street_2", models.TextField(blank=True, null=True)),
                ("city", models.TextField(blank=True, null=True)),
                ("state", models.TextField(blank=True, null=True)),
                ("zip", models.TextField(blank=True, null=True)),
                ("treasurer_last_name", models.TextField(blank=True, null=True)),
                ("treasurer_first_name", models.TextField(blank=True, null=True)),
                ("treasurer_middle_name", models.TextField(blank=True, null=True)),
                ("treasurer_prefix", models.TextField(blank=True, null=True)),
                ("treasurer_suffix", models.TextField(blank=True, null=True)),
                ("date_signed", models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.AlterField(
            model_name="reportf3x",
            name="calculation_status",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="report",
            name="report_f24",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="reports.reportf24",
            ),
        ),
    ]
