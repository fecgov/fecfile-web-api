# Generated by Django 4.2.11 on 2024-07-02 17:21

from django.db import migrations, models
from django.db import connection


def populate_existing_rows(apps, schema_editor):
    report_model = apps.get_model("reports", "Report")
    for row in report_model.objects.all():
        row.can_delete = True
        row.save()


def create_trigger(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        CREATE OR REPLACE FUNCTION check_can_delete()
        RETURNS TRIGGER AS $$
        BEGIN
            PERFORM update_report_can_delete(NEW);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION check_can_delete_previous()
        RETURNS TRIGGER AS $$
        DECLARE
            associated_report RECORD;
        BEGIN
            FOR associated_report IN (
                SELECT * FROM reports_report
                WHERE committee_account_id = OLD.committee_account_id
                AND can_delete = false
            )
            LOOP
                PERFORM update_report_can_delete(associated_report);
            END LOOP;

            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;


        CREATE OR REPLACE FUNCTION check_can_delete_transaction_update()
        RETURNS TRIGGER AS $$
        DECLARE
            associated_report RECORD;
        BEGIN
            SELECT * INTO associated_report FROM reports_report WHERE id IN (
                    SELECT report_id FROM reports_reporttransaction
                    WHERE transaction_id = NEW.id LIMIT 1
                );
                PERFORM update_report_can_delete(associated_report);

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION check_can_delete_transaction_insert()
        RETURNS TRIGGER AS $$
        DECLARE
             associated_report RECORD;
        BEGIN
            FOR associated_report IN (
                SELECT r1.*
                FROM reports_report r1
                JOIN reports_report r2
                    ON r1.committee_account_id = r2.committee_account_id
                    AND EXTRACT(YEAR FROM r1.coverage_from_date) = (
                        EXTRACT(YEAR FROM r2.coverage_from_date))
                WHERE r1.can_delete = true
                AND r2.id = NEW.report_id
            )
        LOOP
            PERFORM update_report_can_delete(associated_report);
        END LOOP;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER check_can_delete_report
        AFTER INSERT OR UPDATE ON reports_report
        FOR EACH ROW
        WHEN (pg_trigger_depth() = 0) -- Prevent infinite trigger loop
        EXECUTE FUNCTION check_can_delete();

        CREATE TRIGGER check_can_delete_previous
        AFTER DELETE ON reports_report
        FOR EACH ROW
        WHEN (pg_trigger_depth() = 0) -- Prevent infinite trigger loop
        EXECUTE FUNCTION check_can_delete_previous();

        CREATE TRIGGER check_can_delete_transaction_insert
        AFTER INSERT ON reports_reporttransaction
        FOR EACH ROW
        WHEN (pg_trigger_depth() = 0) -- Prevent infinite trigger loop
        EXECUTE FUNCTION check_can_delete_transaction_insert();
        """
        )


def reverse_code(apps, schema_editor):
    # Get models
    report_model = apps.get_model("reports", "Report")
    transaction_model = apps.get_model("transactions", "Transaction")

    # Drop triggers
    triggers = [
        "check_can_delete_report",
        "check_can_delete_previous",
        "check_can_delete_transaction_update",
        "check_can_delete_transaction_insert",
    ]

    with schema_editor.atomic():
        for trigger in triggers:
            schema_editor.execute(
                "DROP TRIGGER IF EXISTS %s ON %s", (trigger, report_model._meta.db_table)
            )
            schema_editor.execute(
                "DROP TRIGGER IF EXISTS %s ON %s",
                (trigger, transaction_model._meta.db_table),
            )


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0008_remove_form1m_city_remove_form1m_committee_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="can_delete",
            field=models.BooleanField(default=True),
        ),
        migrations.RunSQL(
            """
        CREATE OR REPLACE FUNCTION update_report_can_delete(report RECORD)
        RETURNS VOID AS $$
        DECLARE
            r_can_delete boolean;
        BEGIN
             r_can_delete = report.upload_submission_id IS NULL
                AND (report.report_version IS NULL OR report.report_version = '0')
                AND (
                    report.form_3x_id IS NULL OR
                    (
                        report.form_24_id IS NULL
                        AND NOT EXISTS(
                            SELECT DISTINCT rrt1.id
                            FROM "reports_reporttransaction" rrt1
                                JOIN "transactions_transaction" tt ON (
                                rrt1."transaction_id" = tt."id"
                                OR tt."reatt_redes_id" = rrt1."transaction_id"
                                OR tt."parent_transaction_id" = rrt1."transaction_id"
                                OR tt."debt_id" = rrt1."transaction_id"
                                OR tt."loan_id" = rrt1."transaction_id"
                            )
                                INNER JOIN "reports_reporttransaction" rrt2 ON (
                                rrt2."transaction_id" = tt."id"
                                AND rrt2."report_id" <> report.id
                            )
                            WHERE rrt1."report_id" = report.id
                        )
                    )
                );
            UPDATE reports_report SET can_delete = r_can_delete
            WHERE id = report.id
            AND can_delete <> r_can_delete;
        END;
        $$ LANGUAGE plpgsql;
        """
        ),
        migrations.RunPython(create_trigger, reverse_code),
        migrations.RunPython(populate_existing_rows),
    ]
