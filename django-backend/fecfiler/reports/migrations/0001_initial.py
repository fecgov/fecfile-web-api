# Generated by Django 4.2.7 on 2024-01-16 20:15

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("committee_accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Form1M",
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
                ("committee_name", models.TextField(blank=True, null=True)),
                ("street_1", models.TextField(blank=True, null=True)),
                ("street_2", models.TextField(blank=True, null=True)),
                ("city", models.TextField(blank=True, null=True)),
                ("state", models.TextField(blank=True, null=True)),
                ("zip", models.TextField(blank=True, null=True)),
                (
                    "committee_type",
                    models.CharField(blank=True, max_length=1, null=True),
                ),
                (
                    "affiliated_date_form_f1_filed",
                    models.DateField(blank=True, null=True),
                ),
                (
                    "affiliated_committee_fec_id",
                    models.TextField(blank=True, null=True),
                ),
                ("affiliated_committee_name", models.TextField(blank=True, null=True)),
                ("I_candidate_id_number", models.TextField(blank=True, null=True)),
                ("I_candidate_last_name", models.TextField(blank=True, null=True)),
                ("I_candidate_first_name", models.TextField(blank=True, null=True)),
                ("I_candidate_middle_name", models.TextField(blank=True, null=True)),
                ("I_candidate_prefix", models.TextField(blank=True, null=True)),
                ("I_candidate_suffix", models.TextField(blank=True, null=True)),
                (
                    "I_candidate_office",
                    models.CharField(blank=True, max_length=1, null=True),
                ),
                ("I_candidate_state", models.TextField(blank=True, null=True)),
                ("I_candidate_district", models.TextField(blank=True, null=True)),
                ("I_date_of_contribution", models.DateField(blank=True, null=True)),
                ("II_candidate_id_number", models.TextField(blank=True, null=True)),
                ("II_candidate_last_name", models.TextField(blank=True, null=True)),
                ("II_candidate_first_name", models.TextField(blank=True, null=True)),
                ("II_candidate_middle_name", models.TextField(blank=True, null=True)),
                ("II_candidate_prefix", models.TextField(blank=True, null=True)),
                ("II_candidate_suffix", models.TextField(blank=True, null=True)),
                (
                    "II_candidate_office",
                    models.CharField(blank=True, max_length=1, null=True),
                ),
                ("II_candidate_state", models.TextField(blank=True, null=True)),
                ("II_candidate_district", models.TextField(blank=True, null=True)),
                ("II_date_of_contribution", models.DateField(blank=True, null=True)),
                ("III_candidate_id_number", models.TextField(blank=True, null=True)),
                ("III_candidate_last_name", models.TextField(blank=True, null=True)),
                ("III_candidate_first_name", models.TextField(blank=True, null=True)),
                ("III_candidate_middle_name", models.TextField(blank=True, null=True)),
                ("III_candidate_prefix", models.TextField(blank=True, null=True)),
                ("III_candidate_suffix", models.TextField(blank=True, null=True)),
                (
                    "III_candidate_office",
                    models.CharField(blank=True, max_length=1, null=True),
                ),
                ("III_candidate_state", models.TextField(blank=True, null=True)),
                ("III_candidate_district", models.TextField(blank=True, null=True)),
                ("III_date_of_contribution", models.DateField(blank=True, null=True)),
                ("IV_candidate_id_number", models.TextField(blank=True, null=True)),
                ("IV_candidate_last_name", models.TextField(blank=True, null=True)),
                ("IV_candidate_first_name", models.TextField(blank=True, null=True)),
                ("IV_candidate_middle_name", models.TextField(blank=True, null=True)),
                ("IV_candidate_prefix", models.TextField(blank=True, null=True)),
                ("IV_candidate_suffix", models.TextField(blank=True, null=True)),
                (
                    "IV_candidate_office",
                    models.CharField(blank=True, max_length=1, null=True),
                ),
                ("IV_candidate_state", models.TextField(blank=True, null=True)),
                ("IV_candidate_district", models.TextField(blank=True, null=True)),
                ("IV_date_of_contribution", models.DateField(blank=True, null=True)),
                ("V_candidate_id_number", models.TextField(blank=True, null=True)),
                ("V_candidate_last_name", models.TextField(blank=True, null=True)),
                ("V_candidate_first_name", models.TextField(blank=True, null=True)),
                ("V_candidate_middle_name", models.TextField(blank=True, null=True)),
                ("V_candidate_prefix", models.TextField(blank=True, null=True)),
                ("V_candidate_suffix", models.TextField(blank=True, null=True)),
                (
                    "V_candidate_office",
                    models.CharField(blank=True, max_length=1, null=True),
                ),
                ("V_candidate_state", models.TextField(blank=True, null=True)),
                ("V_candidate_district", models.TextField(blank=True, null=True)),
                ("V_date_of_contribution", models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Form24",
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
                ("report_type_24_48", models.TextField(blank=True, null=True)),
                ("original_amendment_date", models.DateField(blank=True, null=True)),
                ("street_1", models.TextField(blank=True, null=True)),
                ("street_2", models.TextField(blank=True, null=True)),
                ("city", models.TextField(blank=True, null=True)),
                ("state", models.TextField(blank=True, null=True)),
                ("zip", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Form3X",
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
                    "change_of_address",
                    models.BooleanField(blank=True, default=False, null=True),
                ),
                ("street_1", models.TextField(blank=True, null=True)),
                ("street_2", models.TextField(blank=True, null=True)),
                ("city", models.TextField(blank=True, null=True)),
                ("state", models.TextField(blank=True, null=True)),
                ("zip", models.TextField(blank=True, null=True)),
                ("election_code", models.TextField(blank=True, null=True)),
                ("date_of_election", models.DateField(blank=True, null=True)),
                ("state_of_election", models.TextField(blank=True, null=True)),
                (
                    "qualified_committee",
                    models.BooleanField(blank=True, default=False, null=True),
                ),
                ("cash_on_hand_date", models.DateField(blank=True, null=True)),
                (
                    "L6b_cash_on_hand_beginning_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L6c_total_receipts_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L6d_subtotal_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L7_total_disbursements_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L8_cash_on_hand_at_close_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L9_debts_to_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L10_debts_by_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L11ai_itemized_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L11aii_unitemized_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L11aiii_total_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L11b_political_party_committees_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L11c_other_political_committees_pacs_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L11d_total_contributions_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L12_transfers_from_affiliated_other_party_cmtes_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L13_all_loans_received_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L14_loan_repayments_received_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L15_offsets_to_operating_expenditures_refunds_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L16_refunds_of_federal_contributions_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L17_other_federal_receipts_dividends_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L18a_transfers_from_nonfederal_account_h3_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L18b_transfers_from_nonfederal_levin_h5_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L18c_total_nonfederal_transfers_18a_18b_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L19_total_receipts_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L20_total_federal_receipts_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L21ai_federal_share_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L21aii_nonfederal_share_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L21b_other_federal_operating_expenditures_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L21c_total_operating_expenditures_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L22_transfers_to_affiliated_other_party_cmtes_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L23_contributions_to_federal_candidates_cmtes_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L24_independent_expenditures_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L25_coordinated_expend_made_by_party_cmtes_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L26_loan_repayments_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L27_loans_made_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L28a_individuals_persons_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L28b_political_party_committees_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L28c_other_political_committees_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L28d_total_contributions_refunds_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L29_other_disbursements_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L30ai_shared_federal_activity_h6_fed_share_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L30aii_shared_federal_activity_h6_nonfed_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L30b_nonallocable_fed_election_activity_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L30c_total_federal_election_activity_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L31_total_disbursements_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L32_total_federal_disbursements_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L33_total_contributions_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L34_total_contribution_refunds_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L35_net_contributions_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L36_total_federal_operating_expenditures_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L37_offsets_to_operating_expenditures_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L38_net_operating_expenditures_period",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L6a_cash_on_hand_jan_1_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                ("L6a_year_for_above_ytd", models.TextField(blank=True, null=True)),
                (
                    "L6c_total_receipts_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L6d_subtotal_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L7_total_disbursements_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L8_cash_on_hand_close_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L11ai_itemized_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L11aii_unitemized_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L11aiii_total_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L11b_political_party_committees_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L11c_other_political_committees_pacs_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L11d_total_contributions_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L12_transfers_from_affiliated_other_party_cmtes_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L13_all_loans_received_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L14_loan_repayments_received_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L15_offsets_to_operating_expenditures_refunds_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L16_refunds_of_federal_contributions_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L17_other_federal_receipts_dividends_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L18a_transfers_from_nonfederal_account_h3_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L18b_transfers_from_nonfederal_levin_h5_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L18c_total_nonfederal_transfers_18a_18b_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L19_total_receipts_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L20_total_federal_receipts_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L21ai_federal_share_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L21aii_nonfederal_share_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L21b_other_federal_operating_expenditures_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L21c_total_operating_expenditures_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L22_transfers_to_affiliated_other_party_cmtes_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L23_contributions_to_federal_candidates_cmtes_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L24_independent_expenditures_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L25_coordinated_expend_made_by_party_cmtes_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L26_loan_repayments_made_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L27_loans_made_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L28a_individuals_persons_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L28b_political_party_committees_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L28c_other_political_committees_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L28d_total_contributions_refunds_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L29_other_disbursements_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L30ai_shared_federal_activity_h6_fed_share_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L30aii_shared_federal_activity_h6_nonfed_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L30b_nonallocable_fed_election_activity_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L30c_total_federal_election_activity_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L31_total_disbursements_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L32_total_federal_disbursements_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L33_total_contributions_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L34_total_contribution_refunds_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L35_net_contributions_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L36_total_federal_operating_expenditures_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L37_offsets_to_operating_expenditures_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
                (
                    "L38_net_operating_expenditures_ytd",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=11, null=True
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Form99",
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
                ("committee_name", models.TextField(blank=True, null=True)),
                ("street_1", models.TextField(blank=True, null=True)),
                ("street_2", models.TextField(blank=True, null=True)),
                ("city", models.TextField(blank=True, null=True)),
                ("state", models.TextField(blank=True, null=True)),
                ("zip", models.TextField(blank=True, null=True)),
                ("text_code", models.TextField(blank=True, null=True)),
                ("message_text", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Report",
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
                ("form_type", models.TextField(blank=True, null=True)),
                ("report_version", models.TextField(blank=True, null=True)),
                ("report_id", models.TextField(blank=True, null=True)),
                ("report_code", models.TextField(blank=True, null=True)),
                ("coverage_from_date", models.DateField(blank=True, null=True)),
                ("coverage_through_date", models.DateField(blank=True, null=True)),
                ("treasurer_last_name", models.TextField(blank=True, null=True)),
                ("treasurer_first_name", models.TextField(blank=True, null=True)),
                ("treasurer_middle_name", models.TextField(blank=True, null=True)),
                ("treasurer_prefix", models.TextField(blank=True, null=True)),
                ("treasurer_suffix", models.TextField(blank=True, null=True)),
                ("date_signed", models.DateField(blank=True, null=True)),
                (
                    "calculation_status",
                    models.CharField(blank=True, max_length=255, null=True),
                ),
                (
                    "calculation_token",
                    models.UUIDField(blank=True, default=None, null=True),
                ),
                (
                    "confirmation_email_1",
                    models.EmailField(
                        blank=True, default=None, max_length=44, null=True
                    ),
                ),
                (
                    "confirmation_email_2",
                    models.EmailField(
                        blank=True, default=None, max_length=44, null=True
                    ),
                ),
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
                    "form_1m",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="reports.form1m",
                    ),
                ),
                (
                    "form_24",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="reports.form24",
                    ),
                ),
                (
                    "form_3x",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="reports.form3x",
                    ),
                ),
                (
                    "form_99",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="reports.form99",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
