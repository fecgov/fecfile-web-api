# Generated by Django 4.2.11 on 2024-05-21 20:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0007_schedulee_so_candidate_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="_calendar_ytd_per_election_office",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=11, null=True
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="aggregate",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=11, null=True
            ),
        ),
        migrations.AddField(
            model_name="transaction",
            name="loan_payment_to_date",
            field=models.DecimalField(
                blank=True, decimal_places=2, max_digits=11, null=True
            ),
        ),

        migrations.RunSQL("""
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        """),

        migrations.RunSQL("""
        CREATE OR REPLACE FUNCTION calculate_entity_aggregates(
            txn RECORD,
            sql_committee_id TEXT,
            temp_table_name TEXT
        )
        RETURNS VOID AS $$
        DECLARE
            schedule_date DATE;
        BEGIN
            IF txn.schedule_a_id IS NOT NULL THEN
                SELECT contribution_date
                INTO schedule_date
                FROM transactions_schedulea
                WHERE id = txn.schedule_a_id;
            ELSIF txn.schedule_b_id IS NOT NULL THEN
                SELECT expenditure_date
                INTO schedule_date
                FROM transactions_scheduleb
                WHERE id = txn.schedule_b_id;
            END IF;

            EXECUTE '
                CREATE TEMPORARY TABLE ' || temp_table_name || '
                ON COMMIT DROP AS
                SELECT
                    id,
                    SUM(effective_amount) OVER (ORDER BY date, created)
                    AS new_sum
                FROM transaction_view__' || sql_committee_id || '
                WHERE
                    contact_1_id = $1
                    AND EXTRACT(YEAR FROM date) = $2
                    AND aggregation_group = $3
                    AND force_unaggregated IS NOT TRUE;

                UPDATE transactions_transaction AS t
                SET aggregate = tt.new_sum
                FROM ' || temp_table_name || ' AS tt
                WHERE t.id = tt.id;
            '
            USING
                txn.contact_1_id,
                EXTRACT(YEAR FROM schedule_date),
                txn.aggregation_group;
        END;
        $$ LANGUAGE plpgsql;
        """),

        migrations.RunSQL("""
        CREATE OR REPLACE FUNCTION calculate_calendar_ytd_per_election_office(
            txn RECORD,
            sql_committee_id TEXT,
            temp_table_name TEXT
        )
        RETURNS VOID AS $$
        DECLARE
            schedule_date DATE;
            v_election_code TEXT;
            v_candidate_office TEXT;
            v_candidate_state TEXT;
            v_candidate_district TEXT;
        BEGIN
            SELECT COALESCE(disbursement_date, dissemination_date)
                INTO schedule_date FROM transactions_schedulee
                WHERE id = txn.schedule_e_id;
            SELECT election_code
                INTO v_election_code
                FROM transactions_schedulee
                WHERE id = txn.schedule_e_id;
            SELECT candidate_office, candidate_state, candidate_district
                INTO v_candidate_office, v_candidate_state, v_candidate_district
                FROM contacts WHERE id = txn.contact_2_id;

            EXECUTE '
                CREATE TEMPORARY TABLE ' || temp_table_name || '
                ON COMMIT DROP AS
                SELECT
                    t.id,
                    SUM(t.effective_amount) OVER
                    (ORDER BY t.date, t.created) AS new_sum
                FROM transactions_schedulee e
                    JOIN transaction_view__' || sql_committee_id || ' t
                        ON e.id = t.schedule_e_id
                    JOIN contacts c
                        ON t.contact_2_id = c.id
                WHERE
                    e.election_code  = $1
                    AND c.candidate_office = $2
                    AND (
                        c.candidate_state = $3
                        OR (
                            c.candidate_state IS NULL
                            AND $3 = ''''
                        )
                    )
                    AND (
                        c.candidate_district = $4
                        OR (
                            c.candidate_district IS NULL
                            AND $4 = ''''
                        )
                    )
                    AND EXTRACT(YEAR FROM t.date) = $5
                    AND aggregation_group = $6
                    AND force_unaggregated IS NOT TRUE;

                UPDATE transactions_transaction AS t
                SET _calendar_ytd_per_election_office = tt.new_sum
                FROM ' || temp_table_name || ' AS tt
                WHERE t.id = tt.id;
            '
            USING
                v_election_code,
                v_candidate_office,
                COALESCE(v_candidate_state, ''),
                COALESCE(v_candidate_district, ''),
                EXTRACT(YEAR FROM schedule_date),
                txn.aggregation_group;
        END;
        $$ LANGUAGE plpgsql;
        """),

        migrations.RunSQL("""
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
                    SELECT transaction_id FROM transactions_transaction
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
        """),

        migrations.RunSQL("""
        CREATE OR REPLACE FUNCTION calculate_aggregates()
        RETURNS TRIGGER AS $$
        DECLARE
            sql_committee_id TEXT;
            temp_table_name TEXT;
        BEGIN
            sql_committee_id := REPLACE(NEW.committee_account_id::TEXT, '-', '_');
            temp_table_name := 'temp_' || REPLACE(uuid_generate_v4()::TEXT, '-', '_');

            -- RAISE EXCEPTION '%', NEW;

            -- If schedule_c2_id or schedule_d_id is not null, stop processing
            IF NEW.schedule_c2_id IS NOT NULL OR NEW.schedule_d_id IS NOT NULL
            THEN
                RETURN NEW;
            END IF;

            IF NEW.schedule_a_id IS NOT NULL OR NEW.schedule_b_id IS NOT NULL
            THEN
                SELECT calculate_entity_aggregates(NEW, sql_committee_id, temp_table_name);
                IF OLD IS NOT NULL
                    AND NEW.contact_1_id <> OLD.contact_1_id
                THEN
                    SELECT calculate_entity_aggregates(OLD, sql_committee_id, temp_table_name);
                END IF;

            ELSIF NEW.schedule_c_id IS NOT NULL OR NEW.schedule_c1_id IS NOT NULL
            THEN
                SELECT calculate_loan_payment_to_date(NEW, sql_committee_id, temp_table_name);

            ELSIF NEW.schedule_e_id IS NOT NULL
            THEN
                SELECT calculate_calendar_ytd_per_election_office(NEW, sql_committee_id, temp_table_name);
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER calculate_aggregates_trigger
        AFTER INSERT OR UPDATE ON transactions_transaction
        FOR EACH ROW
        WHEN (pg_trigger_depth() = 0) -- Prevent infinite trigger loop
        EXECUTE FUNCTION calculate_aggregates();
        """),
    ]
