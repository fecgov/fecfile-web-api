# Generated by Django 3.2.12 on 2022-04-05 17:11

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('committee_accounts', '__first__'),
        ('f3x_summaries', '0004_auto_20220310_1202'),
    ]

    operations = [
        migrations.AddField(
            model_name='f3xsummary',
            name='committee_account_id',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='committee_accounts.committeeaccount'),
        ),
    ]
