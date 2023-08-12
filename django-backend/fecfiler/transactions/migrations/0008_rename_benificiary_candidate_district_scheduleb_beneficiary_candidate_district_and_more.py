# Generated by Django 4.1.3 on 2023-04-05 16:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0007_create_index_on_form_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='scheduleb',
            old_name='benificiary_candidate_district',
            new_name='beneficiary_candidate_district',
        ),
        migrations.RenameField(
            model_name='scheduleb',
            old_name='benificiary_candidate_fec_id',
            new_name='beneficiary_candidate_fec_id',
        ),
        migrations.RenameField(
            model_name='scheduleb',
            old_name='benificiary_candidate_first_name',
            new_name='beneficiary_candidate_first_name',
        ),
        migrations.RenameField(
            model_name='scheduleb',
            old_name='benificiary_candidate_last_name',
            new_name='beneficiary_candidate_last_name',
        ),
        migrations.RenameField(
            model_name='scheduleb',
            old_name='benificiary_candidate_middle_name',
            new_name='beneficiary_candidate_middle_name',
        ),
        migrations.RenameField(
            model_name='scheduleb',
            old_name='benificiary_candidate_office',
            new_name='beneficiary_candidate_office',
        ),
        migrations.RenameField(
            model_name='scheduleb',
            old_name='benificiary_candidate_prefix',
            new_name='beneficiary_candidate_prefix',
        ),
        migrations.RenameField(
            model_name='scheduleb',
            old_name='benificiary_candidate_state',
            new_name='beneficiary_candidate_state',
        ),
        migrations.RenameField(
            model_name='scheduleb',
            old_name='benificiary_candidate_suffix',
            new_name='beneficiary_candidate_suffix',
        ),
        migrations.RenameField(
            model_name='scheduleb',
            old_name='benificiary_committee_fec_id',
            new_name='beneficiary_committee_fec_id',
        ),
        migrations.RenameField(
            model_name='scheduleb',
            old_name='benificiary_committee_name',
            new_name='beneficiary_committee_name',
        ),
    ]