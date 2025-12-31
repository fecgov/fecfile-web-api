# Generated migration to drop database trigger functions
# This migration moves aggregate calculation from database triggers to Django code

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0023_optimize_calculate_loan_payment_to_date"),
    ]

    operations = [
        migrations.RunSQL(
            """
            -- Drop all aggregate-related triggers from transactions_transaction table
            DROP TRIGGER IF EXISTS calculate_aggregates_trigger ON transactions_transaction;
            DROP TRIGGER IF EXISTS after_transactions_transaction_trigger ON transactions_transaction;
            DROP TRIGGER IF EXISTS after_transactions_transaction_infinite_trigger ON transactions_transaction;
            DROP TRIGGER IF EXISTS before_transactions_transaction_trigger ON transactions_transaction;
            """,
            reverse_sql="""
            -- This SQL is intentionally left empty as we don't want to recreate the triggers
            -- The triggers are now handled by Django signals and the aggregate_service module
            """
        ),
        migrations.RunSQL(
            """
            -- Drop the calculate_entity_aggregates function
            DROP FUNCTION IF EXISTS calculate_entity_aggregates(
                txn RECORD, sql_committee_id TEXT, temp_table_name TEXT
            ) CASCADE;
            """,
            reverse_sql="""
            -- This SQL is intentionally left empty as we don't want to recreate the function
            """
        ),
        migrations.RunSQL(
            """
            -- Drop the calculate_calendar_ytd_per_election_office function
            DROP FUNCTION IF EXISTS calculate_calendar_ytd_per_election_office(
                txn RECORD, sql_committee_id TEXT, temp_table_name TEXT
            ) CASCADE;
            """,
            reverse_sql="""
            -- This SQL is intentionally left empty as we don't want to recreate the function
            """
        ),
        migrations.RunSQL(
            """
            -- Drop the calculate_effective_amount function
            DROP FUNCTION IF EXISTS calculate_effective_amount(
                transaction_type_identifier TEXT, amount NUMERIC, schedule_c_id UUID
            ) CASCADE;
            """,
            reverse_sql="""
            -- This SQL is intentionally left empty as we don't want to recreate the function
            """
        ),
        migrations.RunSQL(
            """
            -- Drop the calculate_amount function if it exists
            DROP FUNCTION IF EXISTS calculate_amount(
                contribution_amount NUMERIC,
                expenditure_amount NUMERIC,
                loan_amount NUMERIC,
                guaranteed_amount NUMERIC,
                schedule_e_expenditure_amount NUMERIC,
                debt_id UUID,
                schedule_d_id UUID
            ) CASCADE;
            """,
            reverse_sql="""
            -- This SQL is intentionally left empty as we don't want to recreate the function
            """
        ),
        migrations.RunSQL(
            """
            -- Drop the calculate_loan_payment_to_date function if it exists
            DROP FUNCTION IF EXISTS calculate_loan_payment_to_date(
                txn RECORD, sql_committee_id TEXT, temp_table_name TEXT
            ) CASCADE;
            """,
            reverse_sql="""
            -- This SQL is intentionally left empty as we don't want to recreate the function
            """
        ),
        migrations.RunSQL(
            """
            -- Drop the trigger handler functions
            DROP FUNCTION IF EXISTS after_transactions_transaction() CASCADE;
            DROP FUNCTION IF EXISTS after_transactions_transaction_infinite() CASCADE;
            DROP FUNCTION IF EXISTS before_transactions_transaction() CASCADE;
            DROP FUNCTION IF EXISTS before_transactions_transaction_insert_or_update() CASCADE;
            DROP FUNCTION IF EXISTS after_transactions_transaction_insert_or_update() CASCADE;
            """,
            reverse_sql="""
            -- This SQL is intentionally left empty as we don't want to recreate the function
            """
        ),
        migrations.RunSQL(
            """
            -- Drop the main calculate_aggregates function that was called by triggers
            DROP FUNCTION IF EXISTS calculate_aggregates(old RECORD, new RECORD, tg_op TEXT) CASCADE;
            DROP FUNCTION IF EXISTS calculate_aggregates() CASCADE;
            """,
            reverse_sql="""
            -- This SQL is intentionally left empty as we don't want to recreate the function
            """
        ),
    ]
