from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0018_schedulef_general_election_year_and_more"),
    ]

    old_election_aggregate_function = """
CREATE OR REPLACE FUNCTION calculate_calendar_ytd_per_election_office(
    txn RECORD, sql_committee_id text
)
RETURNS VOID
AS $$
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
        txn.created;
END;
$$
LANGUAGE plpgsql;
    """

    new_election_aggregate_function = """
CREATE OR REPLACE FUNCTION calculate_calendar_ytd_per_election_office(
    txn RECORD, sql_committee_id text
)
RETURNS VOID
AS $$
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
$$
LANGUAGE plpgsql;
    """

    operations = [
        migrations.RunSQL(
            new_election_aggregate_function, reverse_sql=old_election_aggregate_function
        ),
    ]
