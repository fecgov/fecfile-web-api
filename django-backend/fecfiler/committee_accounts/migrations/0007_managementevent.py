# Generated by Django 5.1.7 on 2025-04-08 20:19

import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('committee_accounts', '0006_alter_membership_committee_account_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommitteeManagementEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('user_uuid', models.UUIDField(editable=False)),
                ('event', models.TextField(editable=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('committee_account', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='committee_accounts.committeeaccount')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
