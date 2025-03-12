from django.db import connection, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0016_schedulef_transaction_contact_4_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            """
            DROP FUNCTION IF EXISTS calculate_entity_aggregates;
            DROP FUNCTION IF EXISTS calculate_calendar_ytd_per_election_office;
            DROP FUNCTION IF EXISTS calculate_aggregates;
            """
        ),
        migrations.RunSQL("""
CREATE OR REPLACE FUNCTION calculate_entity_aggregates(
    txn RECORD, sql_committee_id text, old_date date, new_date date
)
RETURNS VOID AS $$
DECLARE
    schedule_date date;
	earlier_date date;
BEGIN
    IF txn.schedule_a_id IS NOT NULL THEN
        SELECT
            contribution_date INTO schedule_date
        FROM
            transactions_schedulea
        WHERE
            id = txn.schedule_a_id;
    ELSIF txn.schedule_b_id IS NOT NULL THEN
        SELECT
            expenditure_date INTO schedule_date
        FROM
            transactions_scheduleb
        WHERE
            id = txn.schedule_b_id;
    END IF;

    SELECT LEAST(old_date, new_date) INTO earlier_date;
    RAISE WARNING 'Old date: (%)', old_date;
    RAISE WARNING 'new date: (%)', new_date;

    EXECUTE '
        UPDATE transactions_transaction AS t
        SET aggregate = tc.new_sum
        FROM (
            SELECT
                t.id,
                COALESCE(
                    sa.contribution_date,
                    sb.expenditure_date,
                    sc.loan_incurred_date,
                    se.disbursement_date,
                    se.dissemination_date
                ) AS date,
                SUM(
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
                        t.schedule_c_id)
                    ) OVER (
                    ORDER BY
                        COALESCE(
                            sa.contribution_date,
                            sb.expenditure_date,
                            sc.loan_incurred_date,
                            se.disbursement_date,
                            se.dissemination_date
                        ),
                        t.created
                ) AS new_sum
            FROM transactions_transaction t
            LEFT JOIN transactions_schedulea AS sa ON t.schedule_a_id = sa.id
            LEFT JOIN transactions_scheduleb AS sb ON t.schedule_b_id = sb.id
            LEFT JOIN transactions_schedulec AS sc ON t.schedule_c_id = sc.id
            LEFT JOIN transactions_schedulec2 AS sc2 ON t.schedule_c2_id = sc2.id
            LEFT JOIN transactions_schedulee AS se ON t.schedule_e_id = se.id
            LEFT JOIN transactions_scheduled AS sd ON t.schedule_d_id = sd.id
            WHERE
                contact_1_id = $1
                AND EXTRACT(YEAR FROM COALESCE(
                    sa.contribution_date,
                    sb.expenditure_date,
                    sc.loan_incurred_date,
                    se.disbursement_date,
                    se.dissemination_date
                )) IN ($2, $3)
                AND aggregation_group = $4
                AND force_unaggregated IS NOT TRUE
                AND deleted IS NULL
        ) AS tc
        WHERE t.id = tc.id
            AND (
                tc.date > $5
                OR (
                    tc.date = $5
                    AND t.created >= $6
                )
            );
        '
    USING
        txn.contact_1_id,
        EXTRACT(YEAR FROM old_date),
        EXTRACT(YEAR FROM new_date),
        txn.aggregation_group,
        earlier_date,
        txn.created;
END;
$$
LANGUAGE plpgsql;
"""
        ),
        migrations.RunSQL("""
CREATE OR REPLACE FUNCTION calculate_calendar_ytd_per_election_office(
    txn RECORD, sql_committee_id text, old_date date, new_date date
)
RETURNS VOID
AS $$
DECLARE
    schedule_date date;
    v_election_code text;
    v_candidate_office text;
    v_candidate_state text;
    v_candidate_district text;
	earlier_date date;
BEGIN
    SELECT
        COALESCE(disbursement_date, dissemination_date) INTO schedule_date
    FROM transactions_schedulee
    WHERE id = txn.schedule_e_id;

    SELECT election_code INTO v_election_code
    FROM transactions_schedulee
    WHERE id = txn.schedule_e_id;
	
    SELECT LEAST(old_date, new_date) INTO earlier_date;

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
                )) IN ($5, $6)
                AND aggregation_group = $7
                AND force_unaggregated IS NOT TRUE
        ) AS tc
        WHERE t.id = tc.id
        AND (
            tc.date > $8
            OR (
                tc.date = $8
                AND t.created >= $9
            )
        );
    '
    USING
        v_election_code,
        v_candidate_office,
        COALESCE(v_candidate_state, ''),
        COALESCE(v_candidate_district, ''),
        EXTRACT(YEAR FROM old_date),
        EXTRACT(YEAR FROM new_date),
        txn.aggregation_group,
        earlier_date,
        txn.created;
END;
$$
LANGUAGE plpgsql;
    """
        ),
        migrations.RunSQL("""
CREATE OR REPLACE FUNCTION calculate_aggregates()
RETURNS TRIGGER AS $$
DECLARE
    sql_committee_id TEXT;
    new_date DATE;
    old_date DATE;
BEGIN
    sql_committee_id := REPLACE(NEW.committee_account_id::TEXT, '-', '_');

    -- If schedule_c2_id or schedule_d_id is not null, stop processing
    IF NEW.schedule_c2_id IS NOT NULL OR NEW.schedule_d_id IS NOT NULL
    THEN
        RETURN NEW;
    END IF;

    IF OLD.schedule_a_id IS NOT NULL THEN
        SELECT
            contribution_date INTO old_date
        FROM
            transactions_schedulea
        WHERE
            id = OLD.schedule_a_id;
    ELSIF OLD.schedule_b_id IS NOT NULL THEN
        SELECT
            expenditure_date INTO old_date
        FROM
            transactions_scheduleb
        WHERE
            id = OLD.schedule_b_id;
    ELSIF OLD.schedule_e_id IS NOT NULL THEN
        SELECT
            COALESCE(disbursement_date, dissemination_date) INTO old_date
        FROM transactions_schedulee
        WHERE id = OLD.schedule_e_id;
    END IF;

    IF NEW.schedule_a_id IS NOT NULL THEN
        SELECT
            contribution_date INTO new_date
        FROM
            transactions_schedulea
        WHERE
            id = NEW.schedule_a_id;
    ELSIF NEW.schedule_b_id IS NOT NULL THEN
        SELECT
            expenditure_date INTO new_date
        FROM
            transactions_scheduleb
        WHERE
            id = NEW.schedule_b_id;
    ELSIF NEW.schedule_e_id IS NOT NULL THEN
        SELECT
            COALESCE(disbursement_date, dissemination_date) INTO new_date
        FROM transactions_schedulee
        WHERE id = NEW.schedule_e_id;
    END IF;

    IF NEW.schedule_a_id IS NOT NULL OR NEW.schedule_b_id IS NOT NULL
    THEN
        PERFORM calculate_entity_aggregates(NEW, sql_committee_id, old_date, new_date);
        IF TG_OP = 'UPDATE'
            AND NEW.contact_1_id <> OLD.contact_1_id
        THEN
            PERFORM calculate_entity_aggregates(OLD, sql_committee_id, old_date, new_date);
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
            NEW, sql_committee_id, old_date, new_date);
        IF TG_OP = 'UPDATE'
        THEN
            PERFORM calculate_calendar_ytd_per_election_office(
                OLD, sql_committee_id, old_date, new_date);
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
        ),
        migrations.RunSQL(
"""
CREATE OR REPLACE FUNCTION calculate_aggregates(
    OLD RECORD,
    NEW RECORD,
    TG_OP TEXT
)
RETURNS RECORD AS $$
DECLARE
    sql_committee_id TEXT;
    new_date DATE;
    old_date DATE;
BEGIN
    sql_committee_id := REPLACE(NEW.committee_account_id::TEXT, '-', '_');

    -- If schedule_c2_id or schedule_d_id is not null, stop processing
    IF NEW.schedule_c2_id IS NOT NULL OR NEW.schedule_d_id IS NOT NULL
    THEN
        RETURN NEW;
    END IF;

    IF OLD.schedule_a_id IS NOT NULL THEN
        SELECT
            contribution_date INTO old_date
        FROM
            transactions_schedulea
        WHERE
            id = OLD.schedule_a_id;
    ELSIF OLD.schedule_b_id IS NOT NULL THEN
        SELECT
            expenditure_date INTO old_date
        FROM
            transactions_scheduleb
        WHERE
            id = OLD.schedule_b_id;
    ELSIF OLD.schedule_e_id IS NOT NULL THEN
        SELECT
            COALESCE(disbursement_date, dissemination_date) INTO old_date
        FROM transactions_schedulee
        WHERE id = OLD.schedule_e_id;
    END IF;

    IF NEW.schedule_a_id IS NOT NULL THEN
        SELECT
            contribution_date INTO new_date
        FROM
            transactions_schedulea
        WHERE
            id = NEW.schedule_a_id;
    ELSIF NEW.schedule_b_id IS NOT NULL THEN
        SELECT
            expenditure_date INTO new_date
        FROM
            transactions_scheduleb
        WHERE
            id = NEW.schedule_b_id;
    ELSIF NEW.schedule_e_id IS NOT NULL THEN
        SELECT
            COALESCE(disbursement_date, dissemination_date) INTO new_date
        FROM transactions_schedulee
        WHERE id = NEW.schedule_e_id;
    END IF;

    IF NEW.schedule_a_id IS NOT NULL OR NEW.schedule_b_id IS NOT NULL
    THEN
        PERFORM calculate_entity_aggregates(NEW, sql_committee_id, old_date, new_date);
        IF TG_OP = 'UPDATE'
            AND NEW.contact_1_id <> OLD.contact_1_id
        THEN
            PERFORM calculate_entity_aggregates(OLD, sql_committee_id, old_date, new_date);
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
            NEW, sql_committee_id, old_date, new_date);
        IF TG_OP = 'UPDATE'
        THEN
            PERFORM calculate_calendar_ytd_per_election_office(
                OLD, sql_committee_id, old_date, new_date);
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
"""
        )
    ]
