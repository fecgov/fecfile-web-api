# Generated by Django 5.0.8 on 2024-08-20 17:53

from django.db import migrations, models


def create_trigger(apps, schema_editor):
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
        ("reports", "0009_report_can_delete"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="can_unamend",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(create_trigger),
    ]
