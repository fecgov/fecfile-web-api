# Generated by Django 3.2.12 on 2022-04-08 21:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("committee_accounts", "0001_initial"),
        ("scha_transactions", "0005_auto_20220310_1202"),
    ]

    operations = [
        migrations.AddField(
            model_name="schatransaction",
            name="committee_account",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to="committee_accounts.committeeaccount",
            ),
        ),
        migrations.AlterField(
            model_name="schatransaction",
            name="contributor_first_name",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="schatransaction",
            name="contributor_last_name",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="schatransaction",
            name="contributor_organization_name",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="schatransaction",
            name="entity_type",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="schatransaction",
            name="filer_committee_id_number",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="schatransaction",
            name="form_type",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="schatransaction",
            name="transaction_id",
            field=models.TextField(blank=True, null=True),
        ),
    ]
