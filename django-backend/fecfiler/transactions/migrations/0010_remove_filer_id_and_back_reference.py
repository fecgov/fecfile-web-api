# Generated by Django 4.1.3 on 2023-04-27 20:34

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        (
            "transactions",
            "0009_add_force_itemized",  # noqa
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="transaction",
            name="filer_committee_id_number",
        ),
        migrations.RemoveField(
            model_name="transaction",
            name="back_reference_sched_name",
        ),
        migrations.RemoveField(
            model_name="transaction",
            name="back_reference_tran_id_number",
        ),
    ]