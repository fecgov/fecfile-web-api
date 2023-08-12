# Generated by Django 3.2.11 on 2022-02-10 22:51

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="F3XSummary",
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
                (
                    "form_type",
                    models.CharField(
                        choices=[("F3XN", "F3XN"), ("F3XA", "F3XA"), ("F3XT", "F3XT")],
                        default="F3XN",
                        max_length=255,
                    ),
                ),
                ("filer_committee_id_number", models.CharField(max_length=9)),
                (
                    "committee_name",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                (
                    "change_of_address",
                    models.BooleanField(blank=True, default=False, null=True),
                ),
                ("street_1", models.CharField(blank=True, max_length=34, null=True)),
                ("street_2", models.CharField(blank=True, max_length=34, null=True)),
                ("city", models.CharField(blank=True, max_length=30, null=True)),
                ("state", models.CharField(blank=True, max_length=2, null=True)),
                ("zip", models.CharField(blank=True, max_length=9, null=True)),
                ("report_code", models.CharField(blank=True, max_length=3, null=True)),
                (
                    "election_code",
                    models.CharField(blank=True, max_length=5, null=True),
                ),
                (
                    "date_of_election",
                    models.CharField(blank=True, max_length=8, null=True),
                ),
                (
                    "state_of_election",
                    models.CharField(blank=True, max_length=2, null=True),
                ),
                (
                    "coverage_from_date",
                    models.CharField(blank=True, max_length=8, null=True),
                ),
                (
                    "coverage_through_date",
                    models.CharField(blank=True, max_length=8, null=True),
                ),
                (
                    "qualified_committee",
                    models.BooleanField(blank=True, default=False, null=True),
                ),
                ("treasurer_last_name", models.CharField(max_length=30)),
                ("treasurer_first_name", models.CharField(max_length=20)),
                (
                    "treasurer_middle_name",
                    models.CharField(blank=True, max_length=20, null=True),
                ),
                (
                    "treasurer_prefix",
                    models.CharField(blank=True, max_length=10, null=True),
                ),
                (
                    "treasurer_suffix",
                    models.CharField(blank=True, max_length=10, null=True),
                ),
                ("date_signed", models.CharField(max_length=8)),
                (
                    "L6b_cash_on_hand_beginning_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L6c_total_receipts_period",
                    models.IntegerField(blank=True, null=True),
                ),
                ("L6d_subtotal_period", models.IntegerField(blank=True, null=True)),
                (
                    "L7_total_disbursements_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L8_cash_on_hand_at_close_period",
                    models.IntegerField(blank=True, null=True),
                ),
                ("L9_debts_to_period", models.IntegerField(blank=True, null=True)),
                ("L10_debts_by_period", models.IntegerField(blank=True, null=True)),
                ("L11ai_itemized_period", models.IntegerField(blank=True, null=True)),
                (
                    "L11aii_unitemized_period",
                    models.IntegerField(blank=True, null=True),
                ),
                ("L11aiii_total_period", models.IntegerField(blank=True, null=True)),
                (
                    "L11b_political_party_committees_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L11c_other_political_committees_pacs_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L11d_total_contributions_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L12_transfers_from_affiliated_other_party_cmtes_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L13_all_loans_received_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L14_loan_repayments_received_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L15_offsets_to_operating_expenditures_refunds_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L16_refunds_of_federal_contributions_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L17_other_federal_receipts_dividends_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L18a_transfers_from_nonfederal_account_h3_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L18b_transfers_from_nonfederal_levin_h5_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L18c_total_nonfederal_transfers_18a_18b_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L19_total_receipts_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L20_total_federal_receipts_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L21ai_federal_share_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L21aii_nonfederal_share_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L21b_other_federal_operating_expenditures_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L21c_total_operating_expenditures_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L22_transfers_to_affiliated_other_party_cmtes_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L23_contributions_to_federal_candidates_cmtes_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L24_independent_expenditures_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L25_coordinated_expend_made_by_party_cmtes_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L26_loan_repayments_period",
                    models.IntegerField(blank=True, null=True),
                ),
                ("L27_loans_made_period", models.IntegerField(blank=True, null=True)),
                (
                    "L28a_individuals_persons_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L28b_political_party_committees_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L28c_other_political_committees_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L28d_total_contributions_refunds_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L29_other_disbursements_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L30ai_shared_federal_activity_h6_fed_share_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L30aii_shared_federal_activity_h6_nonfed_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L30b_nonallocable_fed_election_activity_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L30c_total_federal_election_activity_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L31_total_disbursements_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L32_total_federal_disbursements_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L33_total_contributions_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L34_total_contribution_refunds_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L35_net_contributions_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L36_total_federal_operating_expenditures_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L37_offsets_to_operating_expenditures_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L38_net_operating_expenditures_period",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L6a_cash_on_hand_jan_1_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L6a_year_for_above_ytd",
                    models.CharField(blank=True, max_length=4, null=True),
                ),
                ("L6c_total_receipts_ytd", models.IntegerField(blank=True, null=True)),
                ("L6d_subtotal_ytd", models.IntegerField(blank=True, null=True)),
                (
                    "L7_total_disbursements_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L8_cash_on_hand_close_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                ("L11ai_itemized_ytd", models.IntegerField(blank=True, null=True)),
                ("L11aii_unitemized_ytd", models.IntegerField(blank=True, null=True)),
                ("L11aiii_total_ytd", models.IntegerField(blank=True, null=True)),
                (
                    "L11b_political_party_committees_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L11c_other_political_committees_pacs_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L11d_total_contributions_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L12_transfers_from_affiliated_other_party_cmtes_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L13_all_loans_received_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L14_loan_repayments_received_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L15_offsets_to_operating_expenditures_refunds_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L16_refunds_of_federal_contributions_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L17_other_federal_receipts_dividends_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L18a_transfers_from_nonfederal_account_h3_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L18b_transfers_from_nonfederal_levin_h5_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L18c_total_nonfederal_transfers_18a_18b_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                ("L19_total_receipts_ytd", models.IntegerField(blank=True, null=True)),
                (
                    "L20_total_federal_receipts_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                ("L21ai_federal_share_ytd", models.IntegerField(blank=True, null=True)),
                (
                    "L21aii_nonfederal_share_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L21b_other_federal_operating_expenditures_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L21c_total_operating_expenditures_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L22_transfers_to_affiliated_other_party_cmtes_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L23_contributions_to_federal_candidates_cmtes_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L24_independent_expenditures_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L25_coordinated_expend_made_by_party_cmtes_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L26_loan_repayments_made_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                ("L27_loans_made_ytd", models.IntegerField(blank=True, null=True)),
                (
                    "L28a_individuals_persons_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L28b_political_party_committees_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L28c_other_political_committees_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L28d_total_contributions_refunds_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L29_other_disbursements_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L30ai_shared_federal_activity_h6_fed_share_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L30aii_shared_federal_activity_h6_nonfed_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L30b_nonallocable_fed_election_activity_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L30c_total_federal_election_activity_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L31_total_disbursements_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L32_total_federal_disbursements_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L33_total_contributions_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L34_total_contribution_refunds_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L35_net_contributions_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L36_total_federal_operating_expenditures_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L37_offsets_to_operating_expenditures_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                (
                    "L38_net_operating_expenditures_ytd",
                    models.IntegerField(blank=True, null=True),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("updated", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "f3x_summaries",
            },
        ),
    ]