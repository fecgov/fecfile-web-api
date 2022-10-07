# Generated by Django 3.2.12 on 2022-10-03 20:24

from django.db import migrations


def update_transaction_type_identifiers(apps, schema_editor):
    sch_a_transaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa

    identifiers = {
        "JF_TRANSFER_PAC_MEMO": "PAC_JF_TRANSFER_MEMO",
    }

    for transaction in sch_a_transaction.objects.all():
        if update_identifier(transaction, identifiers):
            transaction.save()


def reverse_tid_update(apps, schema_editor):
    sch_a_transaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa

    identifiers = {
        "PAC_JF_TRANSFER_MEMO":"JF_TRANSFER_PAC_MEMO",
    }

    for transaction in sch_a_transaction.objects.all():
        if update_identifier(transaction, identifiers):
            transaction.save()


def update_identifier(transaction, identifiers):
    if (transaction.transaction_type_identifier in identifiers.keys()):
        new_identifier = identifiers[transaction.transaction_type_identifier]
        transaction.transaction_type_identifier = new_identifier
        return True
    return False


def update_purpose_description(transaction, purpose_desc):
    updated = False
    for key in purpose_desc.keys():
        if (transaction.contribution_purpose_descrip):
            if (key in transaction.contribution_purpose_descrip):
                old_desc = transaction.contribution_purpose_descrip
                new_desc = old_desc.replace(key, purpose_desc[key])
                transaction.contribution_purpose_descrip = new_desc
                updated = True
    return updated


class Migration(migrations.Migration):

    dependencies = [
        ('scha_transactions', '0026_schatransaction_aggregation_group'),
    ]

    operations = [
        migrations.RunPython(update_transaction_type_identifiers, reverse_tid_update),
    ]
