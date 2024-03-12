# Generated by Django 4.2.7 on 2024-03-08 16:37

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('committee_accounts', '0003_membership_pending_email_alter_membership_id_and_more'),
        ('transactions', '0002_remove_schedulea_contributor_city_and_more'),
        ('reports', '0005_remove_form1m_iii_candidate_district_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReportTransaction',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('committee_account', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='committee_accounts.committeeaccount')),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='reports.report')),
                ('transaction', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='transactions.transaction')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
