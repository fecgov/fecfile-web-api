# Generated by Django 3.2.12 on 2022-10-03 20:24

from django.db import migrations


def update_transaction_type_identifiers(apps, schema_editor):
    SchATransaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa

    identifiers = {
        "EAR_REC":"EARMARK_RECEIPT",
        "TRIB_REC":"TRIBAL_RECEIPT",
        "INDV_REC":"INDIVIDUAL_RECEIPT",
        "OTH_REC":"OTHER_RECEIPT",
        "JF_TRAN":"JOINT_FUNDRAISING_TRANSFER",
        "JF_TRAN_PAC_MEMO":"JOINT_FUNDRAISING_TRANSFER_PAC_MEMO",
        "OFFSET_TO_OPEX":"OFFSET_TO_OPERATING_EXPENDITURES",
    }

    purpose_descriptions = {
        "JF":"Joint Fundraising",
    }

    for transaction in SchATransaction.objects.all():
        updated_tid = update_identifier(transaction, identifiers)
        updated_cpd = update_purpose_description(transaction, purpose_descriptions)
        if (updated_tid or updated_cpd):
            transaction.save()

def reverse_tid_update(apps, schema_editor):
    SchATransaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa

    identifiers = {
        "EARMARK_RECEIPT":"EAR_REC",
        "TRIBAL_RECEIPT":"TRIB_REC",
        "INDIVIDUAL_RECEIPT":"INDV_REC",
        "OTHER_RECEIPT":"OTH_REC",
        "JOINT_FUNDRAISING_TRANSFER":"JF_TRAN",
        "JOINT_FUNDRAISING_TRANSFER_PAC_MEMO":"JF_TRAN_PAC_MEMO",
        "OFFSET_TO_OPERATING_EXPENDITURES":"OFFSET_TO_OPEX",
    }

    purpose_descriptions = {
        "Joint Fundraising":"JF",
    }

    for transaction in SchATransaction.objects.all():
        updated_tid = update_identifier(transaction, identifiers)
        updated_cpd = update_purpose_description(transaction, purpose_descriptions)
        if (updated_tid or updated_cpd):
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
        if (transaction.contribution_purpose_descrip != None):
            if (key in transaction.contribution_purpose_descrip):
                new_desc = transaction.contribution_purpose_descrip.replace(key, purpose_desc[key])
                transaction.contribution_purpose_descrip = new_desc
                updated = True
    return updated


class Migration(migrations.Migration):

    dependencies = [
        ('scha_transactions', '0024_schatransaction_contact'),
    ]

    operations = [
        migrations.RunPython(update_transaction_type_identifiers, reverse_tid_update),
    ]
