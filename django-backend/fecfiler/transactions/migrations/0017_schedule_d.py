# Generated by Django 4.1.3 on 2023-07-27 20:16

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0016_update_schedulec_fields'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduleD',
            fields=[
                (
                    'id',
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True
                    )
                ),
                ('receipt_line_number', models.TextField(blank=True, null=True)),
                ('creditor_organization_name', models.TextField(blank=True, null=True)),
                ('creditor_last_name', models.TextField(blank=True, null=True)),
                ('creditor_first_name', models.TextField(blank=True, null=True)),
                ('creditor_middle_name', models.TextField(blank=True, null=True)),
                ('creditor_prefix', models.TextField(blank=True, null=True)),
                ('creditor_suffix', models.TextField(blank=True, null=True)),
                ('creditor_street_1', models.TextField(blank=True, null=True)),
                ('creditor_street_2', models.TextField(blank=True, null=True)),
                ('creditor_city', models.TextField(blank=True, null=True)),
                ('creditor_state', models.TextField(blank=True, null=True)),
                ('creditor_zip', models.TextField(blank=True, null=True)),
                (
                    'purpose_of_debt_or_obligation',
                    models.TextField(blank=True, null=True)
                ),
                (
                    'beginning_balance',
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=11,
                        null=True
                    )
                ),
                (
                    'incurred_amount',
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=11,
                        null=True
                    )
                ),
                (
                    'payment_amount',
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=11,
                        null=True
                    )
                ),
                (
                    'balance_at_close',
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=11,
                        null=True
                    )
                ),
            ],
        ),
        migrations.AddField(
            model_name='transaction',
            name='schedule_d',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE, to='transactions.scheduled'
            ),
        ),
    ]
