# Generated by Django 3.2.12 on 2022-04-08 21:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("committee_accounts", "0001_initial"),
        ("contacts", "0005_contact_committee_account"),
    ]

    operations = [
        migrations.AlterField(
            model_name="contact",
            name="committee_account",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="committee_accounts.committeeaccount",
            ),
        ),
    ]
