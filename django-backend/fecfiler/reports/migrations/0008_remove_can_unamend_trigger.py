from django.db import connection, migrations


def drop_trigger_functions(_apps, _schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            "DROP TRIGGER IF EXISTS transaction_updated ON transactions_transaction;"
        )
        cursor.execute(
            "DROP TRIGGER IF EXISTS transaction_created ON reports_reporttransaction;"
        )


def drop_db_functions(_apps, _schema_editor):
    with connection.cursor() as cursor:
        cursor.execute("DROP FUNCTION IF EXISTS update_can_unamend();")
        cursor.execute("DROP FUNCTION IF EXISTS update_can_unamend_new_transaction();")


def _reverse_create_can_unamend_trigger(apps, schema_editor):
    schema_editor.execute(
        """
    CREATE OR REPLACE FUNCTION update_can_unamend()
    RETURNS TRIGGER AS $$
    BEGIN
        UPDATE reports_report
        SET can_unamend = FALSE
        WHERE id IN (
            SELECT report_id
            FROM reports_reporttransaction
            WHERE transaction_id = NEW.id
        );
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER transaction_updated
    AFTER UPDATE ON transactions_transaction
    FOR EACH ROW
    WHEN (pg_trigger_depth() = 0) -- Prevent infinite trigger loop
    EXECUTE FUNCTION update_can_unamend();

    CREATE OR REPLACE FUNCTION update_can_unamend_new_transaction()
    RETURNS TRIGGER AS $$
    BEGIN
        UPDATE reports_report
        SET can_unamend = FALSE
        WHERE id IN (
            SELECT report_id
            FROM reports_reporttransaction
            WHERE id = NEW.id
        );
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    CREATE TRIGGER transaction_created
    AFTER INSERT ON reports_reporttransaction
    FOR EACH ROW
    WHEN (pg_trigger_depth() = 0) -- Prevent infinite trigger loop
    EXECUTE FUNCTION update_can_unamend_new_transaction();
    """
    )


class Migration(migrations.Migration):
    dependencies = [
        ("reports", "0007_remove_report_deleted_squashed_00019_form24_name_fix"),
        (
            "transactions",
            "0002_remove_schedulea_squashed_0026_alter_transaction_itemized"
        ),
    ]

    operations = [
        migrations.RunPython(
            code=drop_trigger_functions,
            reverse_code=_reverse_create_can_unamend_trigger,
        ),
        migrations.RunPython(
            code=drop_db_functions,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
