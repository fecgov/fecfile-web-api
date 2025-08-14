from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0022_schedule_f_aggregation"),
    ]

    operations = [
        migrations.RunSQL(
            """
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
                LEFT JOIN transactions_schedulea sa ON t.schedule_a_id = sa.id
                LEFT JOIN transactions_scheduleb sb ON t.schedule_b_id = sb.id
                LEFT JOIN transactions_schedulec sc ON t.schedule_c_id = sc.id
                LEFT JOIN transactions_schedulec2 sc2 ON t.schedule_c2_id = sc2.id
                LEFT JOIN transactions_schedulee se ON t.schedule_e_id = se.id
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
                    (SELECT loan_id FROM transactions_transaction WHERE id = $1),
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
                    (SELECT loan_id FROM transactions_transaction WHERE id = $1),
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
$$
LANGUAGE plpgsql;
"""
        ),
    ]
