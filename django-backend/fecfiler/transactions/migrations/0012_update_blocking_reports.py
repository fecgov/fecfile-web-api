# Generated by Django 5.0.8 on 2024-08-28 15:19

from django.db import migrations


def create_update_blocking_reports_function(apps, schema_editor):
    schema_editor.execute(
        """
        CREATE OR REPLACE FUNCTION update_blocking_reports()
        RETURNS TRIGGER AS $$
        DECLARE
            committee_id UUID;
            transaction RECORD;
            report RECORD;
            blocking_report_ids UUID[];
            is_repayment BOOLEAN;
        BEGIN
            -- Fetch the committee_id for the new transaction
            SELECT committee_account_id
            INTO committee_id
            FROM transactions_transaction
            WHERE id = NEW.transaction_id;

            IF EXISTS (
                SELECT 1
                FROM transactions_transaction
                WHERE id = NEW.transaction_id
                AND (schedule_c_id IS NOT NULL OR
                    schedule_c1_id IS NOT NULL OR
                    schedule_c2_id IS NOT NULL OR
                    schedule_d_id IS NOT NULL OR
                    transaction_type_identifier LIKE '%%REPAYMENT%%' OR
                    transaction_type_identifier LIKE 'LOAN%%RECEIPT' OR
                    transaction_type_identifier LIKE 'DEBT%%RECEIPT')
            ) THEN
                -- Loop through each transaction with the same committee ID
                -- and a relevant schedule
                FOR transaction IN
                    SELECT id, transaction_type_identifier
                    FROM transactions_transaction
                    WHERE committee_account_id = committee_id
                    AND (schedule_c_id IS NOT NULL OR
                        schedule_c1_id IS NOT NULL OR
                        schedule_c2_id IS NOT NULL OR
                        schedule_d_id IS NOT NULL OR
                        loan_id IS NOT NULL OR
                        debt_id IS NOT NULL OR
                        transaction_type_identifier LIKE 'LOAN%%RECEIPT' OR
                        transaction_type_identifier LIKE 'DEBT%%RECEIPT')
                LOOP
                    -- Determine if the transaction is a repayment
                    is_repayment := transaction.transaction_type_identifier
                        LIKE '%%REPAYMENT%%';

                    -- Loop through each report associated with the current transaction
                    FOR report IN
                        SELECT r.id, r.coverage_through_date
                        FROM reports_report AS r
                        INNER JOIN reports_reporttransaction AS rt
                        ON rt.report_id = r.id
                        WHERE rt.transaction_id = transaction.id
                    LOOP
                        -- Find other reports with the same committee_id and
                        -- form_3x not null
                        -- Ensure that reports are only added if they match the conditions
                        SELECT ARRAY(
                            SELECT DISTINCT r2.id
                            FROM reports_report AS r2
                            WHERE r2.committee_account_id = committee_id
                            AND r2.form_3x_id IS NOT NULL
                            AND r2.id != report.id
                            AND (NOT is_repayment OR
                            r2.coverage_through_date > report.coverage_through_date)
                        ) INTO blocking_report_ids;

                        -- Update the blocking_reports array, ensuring no duplicates
                        IF blocking_report_ids IS NOT NULL THEN
                            UPDATE transactions_transaction
                            SET blocking_reports = ARRAY(
                                SELECT DISTINCT
                                unnest(blocking_reports || blocking_report_ids)
                            )
                            WHERE id = transaction.id;
                        END IF;
                    END LOOP;
                END LOOP;
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )


def create_trigger(apps, schema_editor):
    schema_editor.execute(
        """
        CREATE TRIGGER update_blocking_reports
        AFTER INSERT ON reports_reporttransaction
        FOR EACH ROW EXECUTE FUNCTION update_blocking_reports();
    """
    )


def drop_trigger(apps, schema_editor):
    schema_editor.execute(
        "DROP TRIGGER IF EXISTS update_blocking_reports ON reports_reporttransaction;"
    )


def drop_update_blocking_reports_function(apps, schema_editor):
    schema_editor.execute("DROP FUNCTION IF EXISTS update_blocking_reports()")


class Migration(migrations.Migration):
    dependencies = [
        ("transactions", "0011_transaction_can_delete"),
    ]

    operations = [
        migrations.RunPython(
            create_update_blocking_reports_function, drop_update_blocking_reports_function
        ),
        migrations.RunPython(create_trigger, reverse_code=drop_trigger),
    ]
