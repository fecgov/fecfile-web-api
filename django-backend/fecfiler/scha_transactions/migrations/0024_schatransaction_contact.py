# Generated by Django 3.2.12 on 2022-09-22 21:34

from django.db import migrations, models
import django.db.models.deletion


def add_new_contact_id(apps, schema_editor):
    sch_a_transaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa
    contact = apps.get_model("contacts", "Contact")  # noqa

    for trans in sch_a_transaction.objects.all():
        contactDict = {
            'type': trans.entity_type,
            'committee_account_id': trans.committee_account_id,
            'street_1': trans.contributor_street_1,
            'street_2': trans.contributor_street_2,
            'city': trans.contributor_city,
            'state': trans.contributor_state,
            'zip': trans.contributor_zip
        }
        if trans.entity_type == 'IND':
            contactDict['last_name'] = trans.contributor_last_name
            contactDict['first_name'] = trans.contributor_first_name
            contactDict['middle_name'] = trans.contributor_middle_name
            contactDict['prefix'] = trans.contributor_prefix
            contactDict['suffix'] = trans.contributor_suffix
            contactDict['employer'] = trans.contributor_employer
            contactDict['occupation'] = trans.contributor_occupation
        elif trans.entity_type == 'COM':
            contactDict['committee_id'] = trans.donor_committee_fec_id
            contactDict['name'] = trans.contributor_organization_name
        elif trans.entity_type == 'ORG':
            contactDict['name'] = trans.contributor_organization_name
        retval = contact.objects.create(**contactDict)
        trans.contact_id = retval['id']
        trans.save()


def remove_contact_id(apps, schema_editor):
    sch_a_transaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa
    for trans in sch_a_transaction.objects.all():
        trans.contact_id = None
        trans.save()


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0010_auto_20220915_1309'),
        ('scha_transactions', '0023_auto_20220915_1309'),
    ]

    operations = [
        migrations.AddField(
            model_name='schatransaction',
            name='contact',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='contacts.contact'),
        ),
        migrations.RunPython(add_new_contact_id, remove_contact_id),
    ]
