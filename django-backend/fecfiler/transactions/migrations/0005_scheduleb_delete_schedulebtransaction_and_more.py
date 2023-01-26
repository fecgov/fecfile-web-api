# Generated by Django 4.1.3 on 2023-01-26 21:52

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0004_copy_to_unified_table'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScheduleB',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('payee_organization_name', models.TextField(blank=True, null=True)),
                ('payee_last_name', models.TextField(blank=True, null=True)),
                ('payee_first_name', models.TextField(blank=True, null=True)),
                ('payee_middle_name', models.TextField(blank=True, null=True)),
                ('payee_prefix', models.TextField(blank=True, null=True)),
                ('payee_suffix', models.TextField(blank=True, null=True)),
                ('payee_street_1', models.TextField(blank=True, null=True)),
                ('payee_street_2', models.TextField(blank=True, null=True)),
                ('payee_city', models.TextField(blank=True, null=True)),
                ('payee_state', models.TextField(blank=True, null=True)),
                ('payee_zip', models.TextField(blank=True, null=True)),
                ('expenditure_date', models.DateField(blank=True, null=True)),
                ('expenditure_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=11, null=True)),
                ('expenditure_purpose_descrip', models.TextField(blank=True, null=True)),
                ('election_code', models.TextField(blank=True, null=True)),
                ('election_other_description', models.TextField(blank=True, null=True)),
                ('conduit_name', models.TextField(blank=True, null=True)),
                ('conduit_street_1', models.TextField(blank=True, null=True)),
                ('conduit_street_2', models.TextField(blank=True, null=True)),
                ('conduit_city', models.TextField(blank=True, null=True)),
                ('conduit_state', models.TextField(blank=True, null=True)),
                ('conduit_zip', models.TextField(blank=True, null=True)),
                ('category_code', models.TextField(blank=True, null=True)),
                ('benificiary_committee_fec_id', models.TextField(blank=True, null=True)),
                ('benificiary_committee_name', models.TextField(blank=True, null=True)),
                ('benificiary_candidate_fec_id', models.TextField(blank=True, null=True)),
                ('benificiary_candidate_last_name', models.TextField(blank=True, null=True)),
                ('benificiary_candidate_first_name', models.TextField(blank=True, null=True)),
                ('benificiary_candidate_middle_name', models.TextField(blank=True, null=True)),
                ('benificiary_candidate_prefix', models.TextField(blank=True, null=True)),
                ('benificiary_candidate_suffix', models.TextField(blank=True, null=True)),
                ('benificiary_candidate_office', models.TextField(blank=True, null=True)),
                ('benificiary_candidate_state', models.TextField(blank=True, null=True)),
                ('benificiary_candidate_district', models.TextField(blank=True, null=True)),
                ('memo_text_description', models.TextField(blank=True, null=True)),
                ('reference_to_si_or_sl_system_code_that_identifies_the_account', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.DeleteModel(
            name='ScheduleBTransaction',
        ),
        migrations.AddField(
            model_name='transaction',
            name='schedule_b',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='transactions.scheduleb'),
        ),
    ]
