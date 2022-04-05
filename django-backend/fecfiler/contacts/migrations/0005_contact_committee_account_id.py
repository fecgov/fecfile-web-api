# Generated by Django 3.2.12 on 2022-04-05 17:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('committee_accounts', '__first__'),
        ('contacts', '0004_auto_20220317_1636'),
    ]

    operations = [
        migrations.RunSQL("TRUNCATE TABLE contacts"),
        migrations.AddField(
            model_name='contact',
            name='committee_account_id',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='committee_accounts.committeeaccount'),
        ),
    ]
