from django.db import migrations


def update_existing_rows(apps, schema_editor):
    transaction = apps.get_model("transactions", "Transaction")
    types = [
        "LOAN_RECEIVED_FROM_INDIVIDUAL",
        "LOAN_RECEIVED_FROM BANK",
        "LOAN_BY_COMMITTEE",
    ]
    for row in transaction.objects.filter(transaction_type_identifier__in=types):
        row.save()


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0008_transaction__calendar_ytd_per_election_office_and_more"),
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
        migrations.RunSQL(
            """
        CREATE OR REPLACE FUNCTION calculate_aggregates()
        RETURNS TRIGGER AS $$
        DECLARE
            sql_committee_id TEXT;
            temp_table_name TEXT;
        BEGIN
            sql_committee_id := REPLACE(NEW.committee_account_id::TEXT, '-', '_');
            temp_table_name := 'temp_' || REPLACE(uuid_generate_v4()::TEXT, '-', '_');
            RAISE NOTICE 'TESTING TRIGGER';

            -- If schedule_c2_id or schedule_d_id is not null, stop processing
            IF NEW.schedule_c2_id IS NOT NULL OR NEW.schedule_d_id IS NOT NULL
            THEN
                RETURN NEW;
            END IF;

            IF NEW.schedule_a_id IS NOT NULL OR NEW.schedule_b_id IS NOT NULL
            THEN
                PERFORM calculate_entity_aggregates(
                    NEW, sql_committee_id, temp_table_name || 'NEW');
                IF TG_OP = 'UPDATE'
                    AND NEW.contact_1_id <> OLD.contact_1_id
                THEN
                    PERFORM calculate_entity_aggregates(
                        OLD, sql_committee_id, temp_table_name || 'OLD');
                END IF;
            END IF;

            IF NEW.schedule_c_id IS NOT NULL OR NEW.schedule_c1_id IS NOT NULL OR NEW.transaction_type_identifier = 'LOAN_REPAYMENT_MADE'
            THEN
                PERFORM calculate_loan_payment_to_date(
                    NEW, sql_committee_id, temp_table_name || 'NEW');
            END IF;

            IF NEW.schedule_e_id IS NOT NULL
            THEN
                PERFORM calculate_calendar_ytd_per_election_office(
                    NEW, sql_committee_id, temp_table_name || 'NEW');
                IF TG_OP = 'UPDATE'
                THEN
                    PERFORM calculate_calendar_ytd_per_election_office(
                        OLD, sql_committee_id, temp_table_name || 'OLD');
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        ),
        migrations.RunPython(update_existing_rows),
    ]
