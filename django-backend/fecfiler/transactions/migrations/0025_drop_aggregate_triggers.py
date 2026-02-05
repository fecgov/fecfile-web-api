# Generated migration to drop database trigger functions
# This migration moves aggregate calculation from database triggers to Django code

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0024_scheduled_balance_at_close_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            """
            -- Drop all aggregate-related triggers from
            -- transactions_transaction table
            DROP TRIGGER IF EXISTS calculate_aggregates_trigger
                ON transactions_transaction;
            DROP TRIGGER IF EXISTS after_transactions_transaction_trigger
                ON transactions_transaction;
            DROP TRIGGER IF EXISTS
                after_transactions_transaction_infinite_trigger
                ON transactions_transaction;
            DROP TRIGGER IF EXISTS before_transactions_transaction_trigger
                ON transactions_transaction;
            """,
            reverse_sql="""
            -- Recreate triggers for aggregate calculation
            CREATE TRIGGER before_transactions_transaction_trigger
            BEFORE INSERT OR UPDATE ON transactions_transaction
            FOR EACH ROW
            EXECUTE FUNCTION before_transactions_transaction();

            CREATE TRIGGER after_transactions_transaction_infinite_trigger
            AFTER INSERT OR UPDATE ON transactions_transaction
            FOR EACH ROW
            EXECUTE FUNCTION after_transactions_transaction_infinite();

            CREATE TRIGGER after_transactions_transaction_trigger
            AFTER INSERT OR UPDATE ON transactions_transaction
            FOR EACH ROW
            WHEN (pg_trigger_depth() = 0)
            EXECUTE FUNCTION after_transactions_transaction();
            """,
        ),
        migrations.RunSQL(
            """
            -- Drop the calculate_entity_aggregates function
            DROP FUNCTION IF EXISTS calculate_entity_aggregates(
                txn RECORD, sql_committee_id TEXT, temp_table_name TEXT
            ) CASCADE;
            """,
            reverse_sql="""
            -- Recreate calculate_entity_aggregates function
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
            """,
        ),
        migrations.RunSQL(
            """
            -- Drop the calculate_calendar_ytd_per_election_office function
            DROP FUNCTION IF EXISTS calculate_calendar_ytd_per_election_office(
                txn RECORD, sql_committee_id TEXT, temp_table_name TEXT
            ) CASCADE;
            """,
            reverse_sql="""
            -- Recreate calculate_calendar_ytd_per_election_office function
            CREATE OR REPLACE FUNCTION calculate_calendar_ytd_per_election_office(
                txn RECORD, sql_committee_id text
            )
            RETURNS VOID AS $$
            DECLARE
                schedule_date date;
                v_election_code text;
                v_candidate_office text;
                v_candidate_state text;
                v_candidate_district text;
            BEGIN
                SELECT
                    COALESCE(disbursement_date, dissemination_date) INTO schedule_date
                FROM transactions_schedulee
                WHERE id = txn.schedule_e_id;

                SELECT election_code INTO v_election_code
                FROM transactions_schedulee
                WHERE id = txn.schedule_e_id;

                SELECT
                    candidate_office,
                    candidate_state,
                    candidate_district INTO v_candidate_office,
                    v_candidate_state,
                    v_candidate_district
                FROM contacts
                WHERE id = txn.contact_2_id;
                EXECUTE '
                    UPDATE transactions_transaction AS t
                    SET _calendar_ytd_per_election_office = tc.new_sum
                    FROM (
                        SELECT
                            t.id,
                            Coalesce(
                                e.disbursement_date,
                                e.dissemination_date
                            ) as date,
                            SUM(
                                calculate_effective_amount(
                                    t.transaction_type_identifier,
                                    calculate_amount(
                                        NULL,
                                        NULL,
                                        NULL,
                                        NULL,
                                        e.expenditure_amount,
                                        t.debt_id,
                                        t.schedule_d_id
                                    ),
                                t.schedule_c_id
                                )
                            ) OVER (ORDER BY Coalesce(
                                e.disbursement_date,
                                e.dissemination_date
                            ), t.created) AS new_sum
                        FROM transactions_schedulee e
                            JOIN transactions_transaction t
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
                            AND EXTRACT(YEAR FROM Coalesce(
                                e.disbursement_date,
                                e.dissemination_date
                            )) = $5
                            AND aggregation_group = $6
                            AND force_unaggregated IS NOT TRUE
                            AND t.committee_account_id = $9
                    ) AS tc
                    WHERE t.id = tc.id
                    AND (
                        tc.date > $7
                        OR (
                            tc.date = $7
                            AND t.created >= $8
                        )
                    );
                '
                USING
                    v_election_code,
                    v_candidate_office,
                    COALESCE(v_candidate_state, ''),
                    COALESCE(v_candidate_district, ''),
                    EXTRACT(YEAR FROM schedule_date),
                    txn.aggregation_group,
                    schedule_date,
                    txn.created,
                    txn.committee_account_id;
            END;
            $$ LANGUAGE plpgsql;
            """,
        ),
        migrations.RunSQL(
            """
            -- Drop the calculate_effective_amount function
            DROP FUNCTION IF EXISTS calculate_effective_amount(
                transaction_type_identifier TEXT, amount NUMERIC,
                schedule_c_id UUID
            ) CASCADE;
            """,
            reverse_sql="""
            -- Recreate calculate_effective_amount function
            CREATE OR REPLACE FUNCTION calculate_effective_amount(
                transaction_type_identifier TEXT,
                amount NUMERIC,
                schedule_c_id UUID
            )
            RETURNS NUMERIC AS $$
            DECLARE
                effective_amount NUMERIC;
            BEGIN
                -- Case 1: transaction type is a refund
                IF transaction_type_identifier IN (
                    'TRIBAL_REFUND_NP_HEADQUARTERS_ACCOUNT',
                    'TRIBAL_REFUND_NP_CONVENTION_ACCOUNT',
                    'TRIBAL_REFUND_NP_RECOUNT_ACCOUNT',
                    'INDIVIDUAL_REFUND_NP_HEADQUARTERS_ACCOUNT',
                    'INDIVIDUAL_REFUND_NP_CONVENTION_ACCOUNT',
                    'INDIVIDUAL_REFUND_NP_RECOUNT_ACCOUNT',
                    'REFUND_PARTY_CONTRIBUTION',
                    'REFUND_PARTY_CONTRIBUTION_VOID',
                    'REFUND_PAC_CONTRIBUTION',
                    'REFUND_PAC_CONTRIBUTION_VOID',
                    'INDIVIDUAL_REFUND_NON_CONTRIBUTION_ACCOUNT',
                    'BUSINESS_LABOR_REFUND_NON_CONTRIBUTION_ACCOUNT',
                    'OTHER_COMMITTEE_REFUND_NON_CONTRIBUTION_ACCOUNT',
                    'REFUND_UNREGISTERED_CONTRIBUTION',
                    'REFUND_UNREGISTERED_CONTRIBUTION_VOID',
                    'REFUND_INDIVIDUAL_CONTRIBUTION',
                    'REFUND_INDIVIDUAL_CONTRIBUTION_VOID',
                    'OTHER_COMMITTEE_REFUND_REFUND_NP_HEADQUARTERS_ACCOUNT',
                    'OTHER_COMMITTEE_REFUND_REFUND_NP_CONVENTION_ACCOUNT',
                    'OTHER_COMMITTEE_REFUND_REFUND_NP_RECOUNT_ACCOUNT'
                ) THEN
                    effective_amount := amount * -1;

                -- Case 2: schedule_c exists (return NULL)
                ELSIF schedule_c_id IS NOT NULL THEN
                    effective_amount := NULL;

                -- Default case: return the original amount
                ELSE
                    effective_amount := amount;
                END IF;

                RETURN effective_amount;
            END;
            $$ LANGUAGE plpgsql;
            """,
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
            -- Recreate calculate_amount function
            CREATE OR REPLACE FUNCTION calculate_amount(
                schedule_a_contribution_amount NUMERIC,
                schedule_b_expenditure_amount NUMERIC,
                schedule_c_loan_amount NUMERIC,
                schedule_c2_guaranteed_amount NUMERIC,
                schedule_e_expenditure_amount NUMERIC,
                debt UUID,
                schedule_d_id UUID
            )
            RETURNS NUMERIC AS $$
            DECLARE
                debt_incurred_amount NUMERIC;
            BEGIN
                IF debt IS NOT NULL THEN
                    SELECT sd.incurred_amount
                    INTO debt_incurred_amount
                    FROM transactions_transaction t
                    LEFT JOIN transactions_scheduled sd ON t.schedule_d_id = sd.id
                    WHERE t.id = debt;
                ELSE
                    debt_incurred_amount := NULL;
                END IF;

                RETURN COALESCE(
                    schedule_a_contribution_amount,
                    schedule_b_expenditure_amount,
                    schedule_c_loan_amount,
                    schedule_c2_guaranteed_amount,
                    schedule_e_expenditure_amount,
                    debt_incurred_amount,
                    (SELECT incurred_amount
                     FROM transactions_scheduled
                     WHERE id = schedule_d_id)
                );
            END;
            $$ LANGUAGE plpgsql;
            """,
        ),
        migrations.RunSQL(
            """
            -- Drop the calculate_loan_payment_to_date function if it exists
            DROP FUNCTION IF EXISTS calculate_loan_payment_to_date(
                txn RECORD, sql_committee_id TEXT, temp_table_name TEXT
            ) CASCADE;
            """,
            reverse_sql="""
            -- Recreate calculate_loan_payment_to_date function
            CREATE OR REPLACE FUNCTION public.calculate_loan_payment_to_date(
                txn record, sql_committee_id text
            )
            RETURNS VOID AS $$
            BEGIN
                EXECUTE '
                    UPDATE transactions_transaction AS t
                    SET loan_payment_to_date = tc.new_sum
                    FROM (
                        SELECT
                            data.id,
                            data.original_loan_id,
                            data.is_loan,
                            SUM(data.effective_amount) OVER (
                                PARTITION BY data.original_loan_id
                                ORDER BY data.date
                            ) AS new_sum
                        FROM (
                            SELECT
                                t.id,
                                calculate_loan_date(
                                    t.transaction_id,
                                    t.loan_id,
                                    t.transaction_type_identifier,
                                    t.schedule_c_id,
                                    t.schedule_b_id
                                ) AS date,
                                calculate_original_loan_id(
                                    t.transaction_id,
                                    t.loan_id,
                                    t.transaction_type_identifier,
                                    t.schedule_c_id,
                                    t.schedule_b_id
                                ) AS original_loan_id,
                                calculate_is_loan(
                                    t.loan_id,
                                    t.transaction_type_identifier,
                                    t.schedule_c_id
                                ) AS is_loan,
                                calculate_effective_amount(
                                    t.transaction_type_identifier,
                                    calculate_amount(
                                        sa.contribution_amount,
                                        sb.expenditure_amount,
                                        sc.loan_amount,
                                        sc2.guaranteed_amount,
                                        se.expenditure_amount,
                                        t.debt_id,
                                        t.schedule_d_id
                                    ),
                                    t.schedule_c_id
                                ) AS effective_amount
                            FROM transactions_transaction t
                            LEFT JOIN transactions_schedulea sa
                                ON t.schedule_a_id = sa.id
                            LEFT JOIN transactions_scheduleb sb
                                ON t.schedule_b_id = sb.id
                            LEFT JOIN transactions_schedulec sc
                                ON t.schedule_c_id = sc.id
                            LEFT JOIN transactions_schedulec2 sc2
                                ON t.schedule_c2_id = sc2.id
                            LEFT JOIN transactions_schedulee se
                                ON t.schedule_e_id = se.id
                            WHERE t.deleted IS NULL
                        ) AS data
                        WHERE (data.original_loan_id = (
                            SELECT calculate_original_loan_id(
                                t.transaction_id,
                                t.loan_id,
                                t.transaction_type_identifier,
                                t.schedule_c_id,
                                t.schedule_b_id
                            )
                            FROM transactions_transaction t
                            WHERE t.id = COALESCE(
                                (SELECT loan_id
                                 FROM transactions_transaction
                                 WHERE id = $1),
                                $1
                            )
                        )
                        AND data.date <= (
                            SELECT calculate_loan_date(
                                t.transaction_id,
                                t.loan_id,
                                t.transaction_type_identifier,
                                t.schedule_c_id,
                                t.schedule_b_id
                            )
                            FROM transactions_transaction t
                            WHERE t.id = COALESCE(
                                (SELECT loan_id
                                 FROM transactions_transaction
                                 WHERE id = $1),
                                $1
                            )
                        ))
                        OR data.original_loan_id IN (
                            SELECT t.transaction_id
                            FROM transactions_transaction t
                            WHERE t.schedule_c_id IS NOT NULL
                            AND t.loan_id =  $2
                        )
                    ) AS tc
                    WHERE t.id = tc.id
                    AND tc.is_loan = ''T'';
                '
                USING txn.id, txn.loan_id;
            END;
            $$ LANGUAGE plpgsql;
            """,
        ),
        migrations.RunSQL(
            """
            -- Drop the trigger handler functions
            DROP FUNCTION IF EXISTS after_transactions_transaction()
                CASCADE;
            DROP FUNCTION IF EXISTS
                after_transactions_transaction_infinite() CASCADE;
            DROP FUNCTION IF EXISTS before_transactions_transaction()
                CASCADE;
            DROP FUNCTION IF EXISTS
                before_transactions_transaction_insert_or_update()
                CASCADE;
            DROP FUNCTION IF EXISTS
                after_transactions_transaction_insert_or_update()
                CASCADE;
            """,
            reverse_sql="""
            -- Recreate trigger handler functions
            CREATE OR REPLACE FUNCTION before_transactions_transaction()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW := process_itemization(OLD, NEW);
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE OR REPLACE FUNCTION after_transactions_transaction()
            RETURNS TRIGGER AS $$
            BEGIN
                IF TG_OP = 'UPDATE'
                THEN
                    NEW := calculate_aggregates(OLD, NEW, TG_OP);
                    NEW := update_can_unamend(NEW);
                ELSE
                    NEW := calculate_aggregates(OLD, NEW, TG_OP);
                END IF;

                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE OR REPLACE FUNCTION after_transactions_transaction_infinite()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW := handle_parent_itemization(OLD, NEW);
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """,
        ),
        migrations.RunSQL(
            """
            -- Drop the main calculate_aggregates function that was
            -- called by triggers
            DROP FUNCTION IF EXISTS calculate_aggregates(
                old RECORD, new RECORD, tg_op TEXT
            ) CASCADE;
            DROP FUNCTION IF EXISTS calculate_aggregates() CASCADE;
            """,
            reverse_sql="""
            -- Recreate calculate_aggregates function
            CREATE OR REPLACE FUNCTION calculate_aggregates(
                OLD RECORD,
                NEW RECORD,
                TG_OP TEXT
            )
            RETURNS RECORD AS $$
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
            """,
        ),
    ]
