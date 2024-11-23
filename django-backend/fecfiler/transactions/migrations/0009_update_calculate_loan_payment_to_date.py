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
        CREATE OR REPLACE FUNCTION get_temp_tablename()
        RETURNS TEXT AS $$
        BEGIN
            RETURN 'temp_' || REPLACE(uuid_generate_v4()::TEXT, '-', '_');
        END;
        $$ LANGUAGE plpgsql;
        """
        ),
        migrations.RunSQL(
            """
        CREATE OR REPLACE FUNCTION calculate_entity_aggregates(
            txn RECORD,
            sql_committee_id TEXT
        )
        RETURNS VOID AS $$
        DECLARE
            schedule_date DATE;
            temp_table_name TEXT;
        BEGIN
            temp_table_name := get_temp_tablename();
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
        """
        ),
        migrations.RunSQL(
            """
        CREATE OR REPLACE FUNCTION calculate_calendar_ytd_per_election_office(
            txn RECORD,
            sql_committee_id TEXT
        )
        RETURNS VOID AS $$
        DECLARE
            schedule_date DATE;
            v_election_code TEXT;
            v_candidate_office TEXT;
            v_candidate_state TEXT;
            v_candidate_district TEXT;
            temp_table_name TEXT;
        BEGIN
            temp_table_name := get_temp_tablename();
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
        """
        ),
        migrations.RunSQL(
            """
        CREATE OR REPLACE FUNCTION calculate_loan_payment_to_date(
            txn RECORD,
            sql_committee_id TEXT
        )
        RETURNS VOID AS $$
        DECLARE
            temp_table_name TEXT;
        BEGIN
            temp_table_name := get_temp_tablename();
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
        BEGIN
            sql_committee_id := REPLACE(NEW.committee_account_id::TEXT, '-', '_');

            -- If schedule_c2_id or schedule_d_id is not null, stop processing
            IF NEW.schedule_c2_id IS NOT NULL OR NEW.schedule_d_id IS NOT NULL
            THEN
                RETURN NEW;
            END IF;

            IF NEW.schedule_a_id IS NOT NULL OR NEW.schedule_b_id IS NOT NULL
            THEN
                PERFORM calculate_entity_aggregates(NEW, sql_committee_id);
                IF TG_OP = 'UPDATE'
                    AND NEW.contact_1_id <> OLD.contact_1_id
                THEN
                    PERFORM calculate_entity_aggregates(OLD, sql_committee_id);
                END IF;
            END IF;

            IF NEW.schedule_c_id IS NOT NULL
                OR NEW.schedule_c1_id IS NOT NULL
                OR NEW.transaction_type_identifier = 'LOAN_REPAYMENT_MADE'
            THEN
                PERFORM calculate_loan_payment_to_date(NEW, sql_committee_id);
            END IF;

            IF NEW.schedule_e_id IS NOT NULL
            THEN
                PERFORM calculate_calendar_ytd_per_election_office(
                    NEW, sql_committee_id);
                IF TG_OP = 'UPDATE'
                THEN
                    PERFORM calculate_calendar_ytd_per_election_office(
                        OLD, sql_committee_id);
                END IF;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        ),
        migrations.RunSQL(
            """
        -- Drop  prior versions of these functions
        DROP FUNCTION calculate_entity_aggregates(RECORD, TEXT, TEXT);
        DROP FUNCTION calculate_calendar_ytd_per_election_office(RECORD, TEXT, TEXT);
        DROP FUNCTION calculate_loan_payment_to_date(RECORD, TEXT, TEXT);
        """
        ),
        migrations.RunPython(update_existing_rows),
    ]
