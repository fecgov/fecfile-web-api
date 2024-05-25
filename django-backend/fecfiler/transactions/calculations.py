"""Calculations for transaction aggregated fields.

Aggregation values are being calculated when a transaction is saved and with
raw SQL queries using temporary tables as SQL does not support range window
functions being used in UPDATE queries in the manner we need them. Temporary
tables are more performant than regular tables as Postgres will try to keep
them in memory rather than write them to disk.

The query pattern for the calculation functions is as follows:
    1) Cache the rolling sums in a temporary table.
    2) Limit the rows inserted into the temporary table for the summations
       to just those needed for the calculations.
    3) Use the sums in the temporary table to update the
       transactions_transaction table.
"""
from django.db import connection
import uuid


def get_sql_committee_id(txn):
    """Provide a SQL-safe version of the committee ID."""
    return str(txn.committee_account_id).replace('-', '_')


def get_temporary_table_name():
    """Generate a unique temporary table name."""
    return "temp_" + str(uuid.uuid4()).replace('-', '_')


def get_date(txn):
    """Get the appropriate date field for the transaction based on its
    schedule."""
    if txn.schedule_a:
        return txn.schedule_a.contribution_date
    if txn.schedule_b:
        return txn.schedule_b.expenditure_date
    if txn.schedule_c:
        return txn.schedule_c.loan_incurred_date
    if txn.schedule_e:
        if txn.schedule_e.disbursement_date:
            return txn.schedule_e.disbursement_date
        if txn.schedule_e.dissemination_date:
            return txn.schedule_e.dissemination_date
    raise ValueError("No date field found for transaction (ID: {txn.id})")


def update_calculated_fields(txn):
    if txn.schedule_a or txn.schedule_b:
        calculate_entity_aggregates(txn)
    if txn.schedule_e:
        calculate_election_aggregates(txn)
    if txn.loan_id:
        calculate_loan_payment_to_date(txn)


def calculate_entity_aggregates(txn):
    sql_committee_id = get_sql_committee_id(txn)
    temp_table_name = get_temporary_table_name()

    with connection.cursor() as cursor:
        cursor.execute(f"""
            CREATE TEMPORARY TABLE {temp_table_name}
            ON COMMIT DROP
            AS SELECT
                id,
                SUM(effective_amount)
                    OVER (ORDER BY date, created)
                    AS new_sum
            FROM transaction_view__{sql_committee_id}
            WHERE
                contact_1_id = '{txn.contact_1_id}'
                AND EXTRACT(YEAR FROM date) = '{get_date(txn).year}'
                AND aggregation_group = '{txn.aggregation_group}'
                AND force_unaggregated IS NOT TRUE;

            UPDATE transactions_transaction AS t
            SET aggregate = tt.new_sum
            FROM {temp_table_name} AS tt
            WHERE t.id = tt.id;
        """)


def calculate_election_aggregates(txn):
    sql_committee_id = get_sql_committee_id(txn)
    temp_table_name = get_temporary_table_name()

    with connection.cursor() as cursor:
        cursor.execute(f"""
            CREATE TEMPORARY TABLE {temp_table_name}
            ON COMMIT DROP
            AS SELECT
                t.id,
                SUM(t.effective_amount)
                    OVER (ORDER BY t.date, t.created)
                    AS new_sum
            FROM transactions_schedulee e
                JOIN transaction_view__{sql_committee_id} t
                    ON e.id = t.schedule_e_id
                JOIN contacts c
                    ON t.contact_2_id = c.id
            WHERE
                e.election_code  = '{txn.schedule_e.election_code}'
                AND c.candidate_office = '{txn.contact_2.candidate_office}'
                AND (
                    c.candidate_state = '{txn.contact_2.candidate_state or ""}'
                    OR (
                        c.candidate_state IS NULL
                        AND '{txn.contact_2.candidate_state or ""}' = ''
                    )
                )
                AND (
                    c.candidate_district = '{txn.contact_2.candidate_district or ""}'
                    OR (
                        c.candidate_district IS NULL
                        AND '{txn.contact_2.candidate_district or ""}' = ''
                    )
                )
                AND EXTRACT(YEAR FROM t.date) = '{get_date(txn).year}'
                AND aggregation_group = '{txn.aggregation_group}'
                AND force_unaggregated IS NOT TRUE;

            UPDATE transactions_transaction AS t
            SET _calendar_ytd_per_election_office = tt.new_sum
            FROM {temp_table_name} AS tt
            WHERE t.id = tt.id;
        """)


def calculate_loan_payment_to_date(txn):
    sql_committee_id = get_sql_committee_id(txn)
    temp_table_name = get_temporary_table_name()
    loan_id = txn.loan_id
    
    with connection.cursor() as cursor:
        cursor.execute(f"""
            CREATE TEMPORARY TABLE {temp_table_name}
            ON COMMIT DROP
            AS SELECT
                id,
                loan_key,
                SUM(effective_amount)
                    OVER (ORDER BY loan_key)
                    AS new_sum
            FROM transaction_view__{sql_committee_id}
            WHERE loan_key LIKE (
                SELECT transaction_id FROM transactions_transaction
                WHERE id = '{loan_id}'
            ) || '%';

            UPDATE transactions_transaction AS t
            SET loan_payment_to_date = tt.new_sum
            FROM {temp_table_name} AS tt
            WHERE
                t.id = tt.id
                AND tt.loan_key LIKE '%LOAN';
        """)
