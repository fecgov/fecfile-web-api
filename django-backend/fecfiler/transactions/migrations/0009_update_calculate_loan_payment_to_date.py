from django.db import migrations


def update_existing_rows(apps, schema_editor):
    transaction = apps.get_model("transactions", "Transaction")
    types = [
        'LOAN_RECEIVED_FROM_INDIVIDUAL',
        'LOAN_RECEIVED_FROM BANK',
        'LOAN_BY_COMMITTEE',
    ]
    for row in transaction.objects.filter(transaction_type_identifier__in=types):
        row.save()


class Migration(migrations.Migration):

    dependencies = [
        (
            "transactions",
            "0008_transaction__calendar_ytd_per_election_office_and_more"
        ),
    ]

    operations = [
        migrations.RunSQL(
            """
        CREATE OR REPLACE FUNCTION calculate_loan_payment_to_date(
            txn RECORD,
            sql_committee_id TEXT,
            temp_table_name TEXT
        )
        RETURNS VOID AS $$
        BEGIN
            EXECUTE '
                CREATE TEMPORARY TABLE ' || temp_table_name || '
                ON COMMIT DROP AS
                SELECT
                    id,
                    loan_key,
                    SUM(effective_amount) OVER (ORDER BY loan_key) AS new_sum
                FROM transaction_view__' || sql_committee_id || '
                WHERE loan_key LIKE (
                    SELECT
                        CASE
                            WHEN loan_id IS NULL THEN transaction_id
                            ELSE (
                                SELECT transaction_id
                                FROM transactions_transaction
                                WHERE id = t.loan_id
                            )
                        END
                    FROM transactions_transaction t
                    WHERE id = $1
                ) || ''%%''; -- Match the loan_key with a transaction_id prefix

                UPDATE transactions_transaction AS t
                SET loan_payment_to_date = tt.new_sum
                FROM ' || temp_table_name || ' AS tt
                WHERE t.id = tt.id
                AND tt.loan_key LIKE ''%%LOAN'';
            '
            USING txn.id;
        END;
        $$ LANGUAGE plpgsql;
        """
        ),
        migrations.RunPython(update_existing_rows),
    ]
