# Generated by Django 3.2.12 on 2022-10-07 17:26

from django.db import migrations, models


# Machine-generated dict right here.  Not sure it'd be worth it to break it up
general='General'
np_hq='National Party Headquarters Account'
recount='Recount Account'
non_contribution='Non-Contribution Account'
np_convention='National Party Convention Account'
np_recount='National Party Recount Account'
tid_to_aggregation_groups = {'INDIVIDUAL_RECEIPT': general, 'TRIBAL_RECEIPT': general, 'EARMARK_RECEIPT': general, 'EARMARK_MEMO': general, 'PARTY_RECEIPT': general, 'PAC_RECEIPT': general, 'PAC_EARMARK_RECEIPT': general, 'PAC_EARMARK_MEMO': general, 'TRANSFER': general, 'JOINT_FUNDRAISING_TRANSFER': general, 'INDIVIDUAL_JF_TRANSFER_MEMO': general, 'PARTY_JF_TRANSFER_MEMO': general, 'PAC_JF_TRANSFER_MEMO': general, 'TRIBAL_JF_TRANSFER_MEMO': general, 'PARTNERSHIP_JF_TRANSFER_MEMO': ' DESIGN TBD', 'PARTNERSHIP_INDIVIDUAL_JF_TRANSFER_MEMO': ' DESIGN TBD', 'OFFSET_TO_OPERATING_EXPENDITURES': 'Line 15', 'REFUND_TO_REGISTERED_COMMITTEE': 'Line 16', 'REFUND_TO_UNREGISTERED_COMMITTEE': 'Line 16', 'JF_TRANSFER_NATIONAL_PARTY_CONVENTION_ACCOUNT': np_convention, 'INDIVIDUAL_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO': np_convention, 'PAC_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO': np_convention, 'TRIBAL_NATIONAL_PARTY_CONVENTION_JF_TRANSFER_MEMO': np_convention, 'PARTNERSHIP_CONVENTION_JF_TRANSFER_MEMO': ' DESIGN TBD', 'PARTNERSHIP_INDIVIDUAL_CONVENTION_JF_TRANSFER_MEMO': ' DESIGN TBD', 'INDIVIDUAL_NATIONAL_PARTY_CONVENTION_ACCOUNT': np_convention, 'PARTY_NATIONAL_PARTY_CONVENTION_ACCOUNT': np_convention, 'PAC_NATIONAL_PARTY_CONVENTION_ACCOUNT': np_convention, 'TRIBAL_NATIONAL_PARTY_CONVENTION_ACCOUNT': np_convention, 'JF_TRANSFER_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT': np_hq, 'INDIVIDUAL_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO': np_hq, 'PAC_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO': np_hq, 'TRIBAL_NATIONAL_PARTY_HEADQUARTERS_JF_TRANSFER_MEMO': np_hq, 'PARTNERSHIP_HEADQUARTERS_JF_TRANSFER_MEMO': ' DESIGN TBD', 'PARTNERSHIP_INDIVIDUAL_HEADQUARTERS_JF_TRANSFER_MEMO': ' DESIGN TBD', 'INDIVIDUAL_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT': np_hq, 'PARTY_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT': np_hq, 'PAC_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT': np_hq, 'TRIBAL_NATIONAL_PARTY_HEADQUARTERS_ACCOUNT': np_hq, 'JF_TRANSFER_NATIONAL_PARTY_RECOUNT_ACCOUNT': np_recount, 'INDIVIDUAL_NATIONAL_PARTY_JF_TRANSFER_RECOUNT_MEMO': np_recount, 'PAC_NATIONAL_PARTY_JF_TRANSFER_RECOUNT_MEMO': np_recount, 'TRIBAL_NATIONAL_PARTY_JF_TRANSFER_RECOUNT_MEMO': np_recount, 'PARTNERSHIP_RECOUNT_JF_TRANSFER_MEMO': ' DESIGN TBD', 'PARTNERSHIP_INDIVIDUAL_RECOUNT_JF_TRANSFER_MEMO': ' DESIGN TBD', 'INDIVIDUAL_NATIONAL_PARTY_RECOUNT_ACCOUNT': np_recount, 'PARTY_NATIONAL_PARTY_RECOUNT_ACCOUNT': np_recount, 'PAC_NATIONAL_PARTY_RECOUNT_ACCOUNT': np_recount, 'TRIBAL_NATIONAL_PARTY_RECOUNT_ACCOUNT': np_recount, 'INDIVIDUAL_RECEIPT_NON_CONTRIBUTION_ACCOUNT': non_contribution, 'OTHER_COMMITTEE_NON_CONTRIBUTION_ACCOUNT': non_contribution, 'BUSINESS_LABOR_NON_CONTRIBUTION_ACCOUNT': non_contribution, 'OTHER_RECEIPT': 'Other Receipts', 'INDIVIDUAL_RECOUNT_RECEIPT': recount, 'PARTY_RECOUNT_RECEIPT': recount, 'PAC_RECOUNT_RECEIPT': recount, 'TRIBAL_RECOUNT_RECEIPT': recount}  # noqa


def populate_aggregation_group_fields(apps, _):
    sch_a_transaction = apps.get_model('scha_transactions', 'SchATransaction')  # noqa

    for t in sch_a_transaction.objects.all():
        tid = t.transaction_type_identifier
        if (tid in tid_to_aggregation_groups.keys()):
            t.aggregation_group = tid_to_aggregation_groups[tid]
            t.save()
        else:
            print('\nMissing Transaction Type Identifier!', tid)


def noop(_apps, _):
    # Empty function to pass as a reverse method to RunPython
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('scha_transactions', '0026_auto_20221007_1427'),
    ]

    operations = [
        migrations.AddField(
            model_name='schatransaction',
            name='aggregation_group',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunPython(populate_aggregation_group_fields, noop)
    ]
