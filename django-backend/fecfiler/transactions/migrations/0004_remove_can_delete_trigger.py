from django.db import connection, migrations


def drop_trigger(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute("DROP TRIGGER IF EXISTS report_status_update ON reports_report;")


def drop_trigger_function(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute("DROP FUNCTION IF EXISTS update_transactions_can_delete();")


def _reverse_create_trigger_function(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        CREATE OR REPLACE FUNCTION update_transactions_can_delete() RETURNS TRIGGER AS $$
        BEGIN
            UPDATE transactions_transaction
            SET blocking_reports = CASE
                WHEN NEW.upload_submission_id IS NOT NULL
                THEN array_append(blocking_reports, NEW.id)
                ELSE array_remove(blocking_reports, NEW.id)
            END
            -- all transactions in the submitted report
            WHERE id IN (
                SELECT transaction_id
                FROM reports_reporttransaction
                WHERE report_id = NEW.id
            )
            -- all transactions that are reattributed in the submitted report
            OR id IN (
                SELECT reatt_redes_id
                FROM reports_reporttransaction
                JOIN transactions_transaction tt
                ON reports_reporttransaction.transaction_id = tt.id
                WHERE report_id = NEW.id
            )
            -- all loans that are carried forward in the submitted report
            OR id IN (
                SELECT loan_id
                FROM reports_reporttransaction
                JOIN transactions_transaction tt
                ON reports_reporttransaction.transaction_id = tt.id
                WHERE report_id = NEW.id
            )
            -- all repayments to loans that are carried forward in the submitted report
            OR loan_id IN (
                SELECT loan_id
                FROM reports_reporttransaction
                JOIN transactions_transaction tt
                ON reports_reporttransaction.transaction_id = tt.id
                WHERE report_id = NEW.id AND tt.schedule_c_id IS NOT NULL
            )
            -- all debts that are carried forward in the submitted report
            OR id IN (
                SELECT debt_id
                FROM reports_reporttransaction
                JOIN transactions_transaction tt
                ON reports_reporttransaction.transaction_id = tt.id
                WHERE report_id = NEW.id
            )
            -- all repayments to debts that are carried forward in the submitted report
            OR debt_id IN (
                SELECT debt_id
                FROM reports_reporttransaction
                JOIN transactions_transaction tt
                ON reports_reporttransaction.transaction_id = tt.id
                WHERE report_id = NEW.id AND tt.schedule_d_id IS NOT NULL
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        )


def _reverse_create_trigger(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TRIGGER report_status_update
            AFTER UPDATE OF upload_submission_id ON reports_report
            FOR EACH ROW
            EXECUTE FUNCTION update_transactions_can_delete();
            """
        )


class Migration(migrations.Migration):
    dependencies = [
        (
            "transactions",
            "0003_remove_unused_functions"
        ),
        (
            "reports",
            "0008_remove_can_unamend_trigger"
        ),
    ]

    operations = [
        migrations.RunPython(
            code=drop_trigger,
            reverse_code=_reverse_create_trigger,
        ),
        migrations.RunPython(
            code=drop_trigger_function,
            reverse_code=_reverse_create_trigger_function,
        ),
    ]
