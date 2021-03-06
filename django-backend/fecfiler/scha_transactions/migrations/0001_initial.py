# Generated by Django 3.2.11 on 2022-02-03 01:29

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SchATransaction",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("form_type", models.CharField(max_length=8)),
                ("filer_committee_id_number", models.CharField(max_length=9)),
                ("transaction_id", models.CharField(max_length=20)),
                (
                    "back_reference_tran_id_number",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                (
                    "back_reference_sched_name",
                    models.CharField(blank=True, max_length=8, null=True),
                ),
                ("entity_type", models.CharField(max_length=3)),
                ("contributor_organization_name", models.CharField(max_length=200)),
                ("contributor_last_name", models.CharField(max_length=30)),
                ("contributor_first_name", models.CharField(max_length=20)),
                (
                    "contributor_middle_name",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                (
                    "contributor_prefix",
                    models.CharField(blank=True, max_length=10, null=True),
                ),
                (
                    "contributor_suffix",
                    models.CharField(blank=True, max_length=10, null=True),
                ),
                (
                    "contributor_street_1",
                    models.CharField(blank=True, max_length=34, null=True),
                ),
                (
                    "contributor_street_2",
                    models.CharField(blank=True, max_length=34, null=True),
                ),
                (
                    "contributor_city",
                    models.CharField(blank=True, max_length=30, null=True),
                ),
                (
                    "contributor_state",
                    models.CharField(blank=True, max_length=2, null=True),
                ),
                (
                    "contributor_zip",
                    models.CharField(blank=True, max_length=9, null=True),
                ),
                (
                    "election_code",
                    models.CharField(blank=True, max_length=5, null=True),
                ),
                (
                    "election_other_description",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                ("contribution_date", models.IntegerField(blank=True, null=True)),
                ("contribution_amount", models.IntegerField(blank=True, null=True)),
                ("contribution_aggregate", models.IntegerField(blank=True, null=True)),
                (
                    "contribution_purpose_descrip",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "contributor_employer",
                    models.CharField(blank=True, max_length=38, null=True),
                ),
                (
                    "contributor_occupation",
                    models.CharField(blank=True, max_length=38, null=True),
                ),
                (
                    "donor_committee_fec_id",
                    models.CharField(blank=True, max_length=9, null=True),
                ),
                (
                    "donor_committee_name",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                (
                    "donor_candidate_fec_id",
                    models.CharField(blank=True, max_length=9, null=True),
                ),
                (
                    "donor_candidate_last_name",
                    models.CharField(blank=True, max_length=30, null=True),
                ),
                (
                    "donor_candidate_first_name",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                (
                    "donor_candidate_middle_name",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                (
                    "donor_candidate_prefix",
                    models.CharField(blank=True, max_length=10, null=True),
                ),
                (
                    "donor_candidate_suffix",
                    models.CharField(blank=True, max_length=10, null=True),
                ),
                (
                    "donor_candidate_office",
                    models.CharField(blank=True, max_length=1, null=True),
                ),
                (
                    "donor_candidate_state",
                    models.CharField(blank=True, max_length=2, null=True),
                ),
                (
                    "donor_candidate_district",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "conduit_name",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                (
                    "conduit_street1",
                    models.CharField(blank=True, max_length=34, null=True),
                ),
                (
                    "conduit_street2",
                    models.CharField(blank=True, max_length=34, null=True),
                ),
                (
                    "conduit_city",
                    models.CharField(blank=True, max_length=30, null=True),
                ),
                (
                    "conduit_state",
                    models.CharField(blank=True, max_length=2, null=True),
                ),
                ("conduit_zip", models.CharField(blank=True, max_length=9, null=True)),
                ("memo_code", models.CharField(blank=True, max_length=1, null=True)),
                (
                    "memo_text_description",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "reference_to_si_or_sl_system_code_that_identifies_the_account",
                    models.CharField(blank=True, max_length=9, null=True),
                ),
                (
                    "transaction_type_identifier",
                    models.CharField(blank=True, max_length=12, null=True),
                ),
                ("created", models.DateField(auto_now_add=True)),
                ("updated", models.DateField(auto_now=True)),
            ],
            options={
                "db_table": "scha_transactions",
            },
        ),
    ]
