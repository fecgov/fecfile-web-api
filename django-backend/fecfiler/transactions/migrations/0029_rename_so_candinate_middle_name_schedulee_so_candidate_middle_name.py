# Generated by Django 4.1.3 on 2023-10-24 15:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0028_alter_transaction_report"),
    ]

    operations = [
        migrations.RenameField(
            model_name="schedulee",
            old_name="so_candinate_middle_name",
            new_name="so_candidate_middle_name",
        ),
    ]