# Generated by Django 4.2.7 on 2024-01-16 20:15

from django.db import migrations, models
import django.db.models.deletion
import fecfiler.shared.utilities
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("committee_accounts", "0001_initial"),
        ("contacts", "0001_initial"),
        ("reports", "0001_initial"),
        ("memo_text", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ScheduleA",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "contributor_organization_name",
                    models.TextField(blank=True, null=True),
                ),
                ("contributor_last_name", models.TextField(blank=True, null=True)),
                ("contributor_first_name", models.TextField(blank=True, null=True)),
                ("contributor_middle_name", models.TextField(blank=True, null=True)),
                ("contributor_prefix", models.TextField(blank=True, null=True)),
                ("contributor_suffix", models.TextField(blank=True, null=True)),
                ("contributor_street_1", models.TextField(blank=True, null=True)),
                ("contributor_street_2", models.TextField(blank=True, null=True)),
                ("contributor_city", models.TextField(blank=True, null=True)),
                ("contributor_state", models.TextField(blank=True, null=True)),
                ("contributor_zip", models.TextField(blank=True, null=True)),
                ("contribution_date", models.DateField(blank=True, null=True)),
                (
                    "contribution_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "contribution_purpose_descrip",
                    models.TextField(blank=True, null=True),
                ),
                ("contributor_employer", models.TextField(blank=True, null=True)),
                ("contributor_occupation", models.TextField(blank=True, null=True)),
                ("donor_committee_fec_id", models.TextField(blank=True, null=True)),
                ("donor_committee_name", models.TextField(blank=True, null=True)),
                ("donor_candidate_fec_id", models.TextField(blank=True, null=True)),
                ("donor_candidate_last_name", models.TextField(blank=True, null=True)),
                ("donor_candidate_first_name", models.TextField(blank=True, null=True)),
                (
                    "donor_candidate_middle_name",
                    models.TextField(blank=True, null=True),
                ),
                ("donor_candidate_prefix", models.TextField(blank=True, null=True)),
                ("donor_candidate_suffix", models.TextField(blank=True, null=True)),
                ("donor_candidate_office", models.TextField(blank=True, null=True)),
                ("donor_candidate_state", models.TextField(blank=True, null=True)),
                ("donor_candidate_district", models.TextField(blank=True, null=True)),
                ("election_code", models.TextField(blank=True, null=True)),
                ("election_other_description", models.TextField(blank=True, null=True)),
                ("conduit_name", models.TextField(blank=True, null=True)),
                ("conduit_street_1", models.TextField(blank=True, null=True)),
                ("conduit_street_2", models.TextField(blank=True, null=True)),
                ("conduit_city", models.TextField(blank=True, null=True)),
                ("conduit_state", models.TextField(blank=True, null=True)),
                ("conduit_zip", models.TextField(blank=True, null=True)),
                ("memo_text_description", models.TextField(blank=True, null=True)),
                (
                    "reference_to_si_or_sl_system_code_that_identifies_the_account",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "reattribution_redesignation_tag",
                    models.TextField(blank=True, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ScheduleB",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("payee_organization_name", models.TextField(blank=True, null=True)),
                ("payee_last_name", models.TextField(blank=True, null=True)),
                ("payee_first_name", models.TextField(blank=True, null=True)),
                ("payee_middle_name", models.TextField(blank=True, null=True)),
                ("payee_prefix", models.TextField(blank=True, null=True)),
                ("payee_suffix", models.TextField(blank=True, null=True)),
                ("payee_street_1", models.TextField(blank=True, null=True)),
                ("payee_street_2", models.TextField(blank=True, null=True)),
                ("payee_city", models.TextField(blank=True, null=True)),
                ("payee_state", models.TextField(blank=True, null=True)),
                ("payee_zip", models.TextField(blank=True, null=True)),
                ("expenditure_date", models.DateField(blank=True, null=True)),
                (
                    "expenditure_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "expenditure_purpose_descrip",
                    models.TextField(blank=True, null=True),
                ),
                ("election_code", models.TextField(blank=True, null=True)),
                ("election_other_description", models.TextField(blank=True, null=True)),
                ("conduit_name", models.TextField(blank=True, null=True)),
                ("conduit_street_1", models.TextField(blank=True, null=True)),
                ("conduit_street_2", models.TextField(blank=True, null=True)),
                ("conduit_city", models.TextField(blank=True, null=True)),
                ("conduit_state", models.TextField(blank=True, null=True)),
                ("conduit_zip", models.TextField(blank=True, null=True)),
                ("category_code", models.TextField(blank=True, null=True)),
                (
                    "beneficiary_committee_fec_id",
                    models.TextField(blank=True, null=True),
                ),
                ("beneficiary_committee_name", models.TextField(blank=True, null=True)),
                (
                    "beneficiary_candidate_fec_id",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "beneficiary_candidate_last_name",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "beneficiary_candidate_first_name",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "beneficiary_candidate_middle_name",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "beneficiary_candidate_prefix",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "beneficiary_candidate_suffix",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "beneficiary_candidate_office",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "beneficiary_candidate_state",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "beneficiary_candidate_district",
                    models.TextField(blank=True, null=True),
                ),
                ("memo_text_description", models.TextField(blank=True, null=True)),
                (
                    "reference_to_si_or_sl_system_code_that_identifies_the_account",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "reattribution_redesignation_tag",
                    models.TextField(blank=True, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ScheduleC",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("receipt_line_number", models.TextField(blank=True, null=True)),
                ("lender_organization_name", models.TextField(blank=True, null=True)),
                ("lender_last_name", models.TextField(blank=True, null=True)),
                ("lender_first_name", models.TextField(blank=True, null=True)),
                ("lender_middle_name", models.TextField(blank=True, null=True)),
                ("lender_prefix", models.TextField(blank=True, null=True)),
                ("lender_suffix", models.TextField(blank=True, null=True)),
                ("lender_street_1", models.TextField(blank=True, null=True)),
                ("lender_street_2", models.TextField(blank=True, null=True)),
                ("lender_city", models.TextField(blank=True, null=True)),
                ("lender_state", models.TextField(blank=True, null=True)),
                ("lender_zip", models.TextField(blank=True, null=True)),
                ("election_code", models.TextField(blank=True, null=True)),
                ("election_other_description", models.TextField(blank=True, null=True)),
                (
                    "loan_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                ("loan_incurred_date", models.DateField(blank=True, null=True)),
                ("loan_due_date", models.TextField(blank=True, null=True)),
                ("loan_interest_rate", models.TextField(blank=True, null=True)),
                ("secured", models.BooleanField(blank=True, default=False, null=True)),
                (
                    "personal_funds",
                    models.BooleanField(blank=True, default=False, null=True),
                ),
                ("lender_committee_id_number", models.TextField(blank=True, null=True)),
                ("lender_candidate_id_number", models.TextField(blank=True, null=True)),
                ("lender_candidate_last_name", models.TextField(blank=True, null=True)),
                (
                    "lender_candidate_first_name",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "lender_candidate_middle_name",
                    models.TextField(blank=True, null=True),
                ),
                ("lender_candidate_prefix", models.TextField(blank=True, null=True)),
                ("lender_candidate_suffix", models.TextField(blank=True, null=True)),
                ("lender_candidate_office", models.TextField(blank=True, null=True)),
                ("lender_candidate_state", models.TextField(blank=True, null=True)),
                ("lender_candidate_district", models.TextField(blank=True, null=True)),
                ("memo_text_description", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="ScheduleC1",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("lender_organization_name", models.TextField(blank=True, null=True)),
                ("lender_street_1", models.TextField(blank=True, null=True)),
                ("lender_street_2", models.TextField(blank=True, null=True)),
                ("lender_city", models.TextField(blank=True, null=True)),
                ("lender_state", models.TextField(blank=True, null=True)),
                ("lender_zip", models.TextField(blank=True, null=True)),
                (
                    "loan_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                ("loan_interest_rate", models.TextField(blank=True, null=True)),
                ("loan_incurred_date", models.DateField(blank=True, null=True)),
                ("loan_due_date", models.TextField(blank=True, null=True)),
                (
                    "loan_restructured",
                    models.BooleanField(blank=True, default=False, null=True),
                ),
                (
                    "loan_originally_incurred_date",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "credit_amount_this_draw",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "total_balance",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "others_liable",
                    models.BooleanField(blank=True, default=False, null=True),
                ),
                (
                    "collateral",
                    models.BooleanField(blank=True, default=False, null=True),
                ),
                ("desc_collateral", models.TextField(blank=True, null=True)),
                (
                    "collateral_value_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "perfected_interest",
                    models.BooleanField(blank=True, default=False, null=True),
                ),
                (
                    "future_income",
                    models.BooleanField(blank=True, default=False, null=True),
                ),
                (
                    "desc_specification_of_the_above",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "estimated_value",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "depository_account_established_date",
                    models.DateField(blank=True, null=True),
                ),
                ("ind_name_account_location", models.TextField(blank=True, null=True)),
                ("account_street_1", models.TextField(blank=True, null=True)),
                ("account_street_2", models.TextField(blank=True, null=True)),
                ("account_city", models.TextField(blank=True, null=True)),
                ("account_state", models.TextField(blank=True, null=True)),
                ("account_zip", models.TextField(blank=True, null=True)),
                (
                    "dep_acct_auth_date_presidential",
                    models.DateField(blank=True, null=True),
                ),
                ("basis_of_loan_description", models.TextField(blank=True, null=True)),
                ("treasurer_last_name", models.TextField(blank=True, null=True)),
                ("treasurer_first_name", models.TextField(blank=True, null=True)),
                ("treasurer_middle_name", models.TextField(blank=True, null=True)),
                ("treasurer_prefix", models.TextField(blank=True, null=True)),
                ("treasurer_suffix", models.TextField(blank=True, null=True)),
                ("treasurer_date_signed", models.DateField(blank=True, null=True)),
                ("authorized_last_name", models.TextField(blank=True, null=True)),
                ("authorized_first_name", models.TextField(blank=True, null=True)),
                ("authorized_middle_name", models.TextField(blank=True, null=True)),
                ("authorized_prefix", models.TextField(blank=True, null=True)),
                ("authorized_suffix", models.TextField(blank=True, null=True)),
                ("authorized_title", models.TextField(blank=True, null=True)),
                ("authorized_date_signed", models.DateField(blank=True, null=True)),
                (
                    "line_of_credit",
                    models.BooleanField(blank=True, default=False, null=True),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ScheduleC2",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("guarantor_last_name", models.TextField(blank=True, null=True)),
                ("guarantor_first_name", models.TextField(blank=True, null=True)),
                ("guarantor_middle_name", models.TextField(blank=True, null=True)),
                ("guarantor_prefix", models.TextField(blank=True, null=True)),
                ("guarantor_suffix", models.TextField(blank=True, null=True)),
                ("guarantor_street_1", models.TextField(blank=True, null=True)),
                ("guarantor_street_2", models.TextField(blank=True, null=True)),
                ("guarantor_city", models.TextField(blank=True, null=True)),
                ("guarantor_state", models.TextField(blank=True, null=True)),
                ("guarantor_zip", models.TextField(blank=True, null=True)),
                ("guarantor_employer", models.TextField(blank=True, null=True)),
                ("guarantor_occupation", models.TextField(blank=True, null=True)),
                (
                    "guaranteed_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ScheduleD",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("receipt_line_number", models.TextField(blank=True, null=True)),
                ("creditor_organization_name", models.TextField(blank=True, null=True)),
                ("creditor_last_name", models.TextField(blank=True, null=True)),
                ("creditor_first_name", models.TextField(blank=True, null=True)),
                ("creditor_middle_name", models.TextField(blank=True, null=True)),
                ("creditor_prefix", models.TextField(blank=True, null=True)),
                ("creditor_suffix", models.TextField(blank=True, null=True)),
                ("creditor_street_1", models.TextField(blank=True, null=True)),
                ("creditor_street_2", models.TextField(blank=True, null=True)),
                ("creditor_city", models.TextField(blank=True, null=True)),
                ("creditor_state", models.TextField(blank=True, null=True)),
                ("creditor_zip", models.TextField(blank=True, null=True)),
                (
                    "purpose_of_debt_or_obligation",
                    models.TextField(blank=True, null=True),
                ),
                (
                    "incurred_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="ScheduleE",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("payee_organization_name", models.TextField(blank=True, null=True)),
                ("payee_last_name", models.TextField(blank=True, null=True)),
                ("payee_first_name", models.TextField(blank=True, null=True)),
                ("payee_middle_name", models.TextField(blank=True, null=True)),
                ("payee_prefix", models.TextField(blank=True, null=True)),
                ("payee_suffix", models.TextField(blank=True, null=True)),
                ("payee_street_1", models.TextField(blank=True, null=True)),
                ("payee_street_2", models.TextField(blank=True, null=True)),
                ("payee_city", models.TextField(blank=True, null=True)),
                ("payee_state", models.TextField(blank=True, null=True)),
                ("payee_zip", models.TextField(blank=True, null=True)),
                ("election_code", models.TextField(blank=True, null=True)),
                ("election_other_description", models.TextField(blank=True, null=True)),
                ("dissemination_date", models.DateField(blank=True, null=True)),
                (
                    "expenditure_amount",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                ("disbursement_date", models.DateField(blank=True, null=True)),
                (
                    "expenditure_purpose_descrip",
                    models.TextField(blank=True, null=True),
                ),
                ("category_code", models.TextField(blank=True, null=True)),
                ("payee_cmtte_fec_id_number", models.TextField(blank=True, null=True)),
                ("support_oppose_code", models.TextField(blank=True, null=True)),
                ("so_candidate_id_number", models.TextField(blank=True, null=True)),
                ("so_candidate_last_name", models.TextField(blank=True, null=True)),
                ("so_candidate_first_name", models.TextField(blank=True, null=True)),
                ("so_candidate_middle_name", models.TextField(blank=True, null=True)),
                ("so_candidate_prefix", models.TextField(blank=True, null=True)),
                ("so_candidate_suffix", models.TextField(blank=True, null=True)),
                ("so_candidate_office", models.TextField(blank=True, null=True)),
                ("so_candidate_district", models.TextField(blank=True, null=True)),
                ("so_candidate_state", models.TextField(blank=True, null=True)),
                ("completing_last_name", models.TextField(blank=True, null=True)),
                ("completing_first_name", models.TextField(blank=True, null=True)),
                ("completing_middle_name", models.TextField(blank=True, null=True)),
                ("completing_prefix", models.TextField(blank=True, null=True)),
                ("completing_suffix", models.TextField(blank=True, null=True)),
                ("date_signed", models.DateField(blank=True, null=True)),
                ("memo_text_description", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                (
                    "transaction_type_identifier",
                    models.TextField(blank=True, null=True),
                ),
                ("aggregation_group", models.TextField(blank=True, null=True)),
                ("_form_type", models.TextField(blank=True, null=True)),
                (
                    "transaction_id",
                    models.TextField(
                        default=fecfiler.shared.utilities.generate_fec_uid
                    ),
                ),
                ("entity_type", models.TextField(blank=True, null=True)),
                (
                    "memo_code",
                    models.BooleanField(blank=True, default=False, null=True),
                ),
                ("force_itemized", models.BooleanField(blank=True, null=True)),
                ("force_unaggregated", models.BooleanField(blank=True, null=True)),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
                (
                    "committee_account",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="committee_accounts.committeeaccount",
                    ),
                ),
                (
                    "contact_1",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contact_1_transaction_set",
                        to="contacts.contact",
                    ),
                ),
                (
                    "contact_2",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contact_2_transaction_set",
                        to="contacts.contact",
                    ),
                ),
                (
                    "contact_3",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="contact_3_transaction_set",
                        to="contacts.contact",
                    ),
                ),
                (
                    "debt",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="debt_associations",
                        to="transactions.transaction",
                    ),
                ),
                (
                    "loan",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="loan_associations",
                        to="transactions.transaction",
                    ),
                ),
                (
                    "memo_text",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="memo_text.memotext",
                    ),
                ),
                (
                    "parent_transaction",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transactions.transaction",
                    ),
                ),
                (
                    "reatt_redes",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reatt_redes_associations",
                        to="transactions.transaction",
                    ),
                ),
                (
                    "report",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="reports.report",
                    ),
                ),
                (
                    "schedule_a",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transactions.schedulea",
                    ),
                ),
                (
                    "schedule_b",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transactions.scheduleb",
                    ),
                ),
                (
                    "schedule_c",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transactions.schedulec",
                    ),
                ),
                (
                    "schedule_c1",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transactions.schedulec1",
                    ),
                ),
                (
                    "schedule_c2",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transactions.schedulec2",
                    ),
                ),
                (
                    "schedule_d",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transactions.scheduled",
                    ),
                ),
                (
                    "schedule_e",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="transactions.schedulee",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(
                        fields=["_form_type"], name="transaction__form_t_e73a46_idx"
                    )
                ],
            },
        ),
    ]
