from django.db import connection, migrations


def create_triggers(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        CREATE TRIGGER before_transactions_transaction_insert_trigger
        BEFORE INSERT ON transactions_transaction
        FOR EACH ROW
        EXECUTE FUNCTION before_transactions_transaction_insert();

        CREATE TRIGGER before_transactions_transaction_update_trigger
        BEFORE UPDATE ON transactions_transaction
        FOR EACH ROW
        EXECUTE FUNCTION before_transactions_transaction_update();

        CREATE TRIGGER after_transactions_transaction_insert_trigger
        AFTER INSERT ON transactions_transaction
        FOR EACH ROW
        WHEN (pg_trigger_depth() = 0) -- Prevent infinite trigger loop
        EXECUTE FUNCTION after_transactions_transaction_insert();

        CREATE TRIGGER after_transactions_transaction_update_trigger
        AFTER UPDATE ON transactions_transaction
        FOR EACH ROW
        WHEN (pg_trigger_depth() = 0) -- Prevent infinite trigger loop
        EXECUTE FUNCTION after_transactions_transaction_update();

        CREATE TRIGGER after_transactions_transaction_infinite_insert_trigger
        AFTER INSERT ON transactions_transaction
        FOR EACH ROW
        EXECUTE FUNCTION after_transactions_transaction_infinite_insert();

        CREATE TRIGGER after_transactions_transaction_update_infinite_trigger
        AFTER UPDATE ON transactions_transaction
        FOR EACH ROW
        EXECUTE FUNCTION after_transactions_transaction_infinite_update();
        """
        )


def before_transactions_transaction_insert(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        CREATE OR REPLACE FUNCTION before_transactions_transaction_insert()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW := process_itemization(OLD, NEW);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
            """
        )


def before_transactions_transaction_update(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        CREATE OR REPLACE FUNCTION before_transactions_transaction_update()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW := process_itemization(OLD, NEW);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
            """
        )


def after_transactions_transaction_insert(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        CREATE OR REPLACE FUNCTION after_transactions_transaction_insert()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW := calculate_aggregates(OLD, NEW, TG_OP);

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION after_transactions_transaction_infinite_insert()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW := handle_parent_itemization(OLD, NEW);

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
            """
        )


def after_transactions_transaction_update(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        CREATE OR REPLACE FUNCTION after_transactions_transaction_update()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW := calculate_aggregates(OLD, NEW, TG_OP);
            NEW := update_can_unamend(NEW);

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION after_transactions_transaction_infinite_update()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW := handle_parent_itemization(OLD, NEW);

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
            """
        )


def drop_old_triggers(apps, schema_editor):
    schema_editor.execute(
        """
        DROP TRIGGER
        IF EXISTS zafter_transactions_transaction_insert_or_update_trigger
        ON transactions_transaction;

        DROP TRIGGER
        IF EXISTS before_transactions_transaction_insert_or_update_trigger
        ON transactions_transaction;

        DROP TRIGGER
        IF EXISTS transaction_updated
        ON transactions_transaction;

        DROP TRIGGER
        IF EXISTS calculate_aggregates_trigger
        ON transactions_transaction;
        """
    )


def drop_old_functions(apps, schema_editor):
    schema_editor.execute(
        """
        DROP FUNCTION IF EXISTS before_transactions_transaction_insert_or_update;
        DROP FUNCTION IF EXISTS after_transactions_transaction_insert_or_update;
        DROP FUNCTION IF EXISTS calculate_aggregates;
        DROP FUNCTION IF EXISTS update_can_unamend;
        """
    )


#  Replaces old before_transactions_transaction_insert_or_update()
def process_itemization(apps, schema):
    with connection.cursor() as cursor:
        cursor.execute(
            """
    CREATE OR REPLACE FUNCTION process_itemization(
        OLD RECORD,
        NEW RECORD
    )
        RETURNS RECORD AS $$
        DECLARE
            needs_itemized_set boolean;
            itemization boolean;
        BEGIN
            needs_itemized_set := needs_itemized_set(OLD, NEW);
            IF needs_itemized_set THEN
                NEW.itemized := calculate_itemization(NEW);
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        )


# Replaces old after_transactions_transaction_insert_or_update()
def handle_parent_itemization(apps, schema):
    with connection.cursor() as cursor:
        cursor.execute(
            """
    CREATE OR REPLACE FUNCTION handle_parent_itemization(
        OLD RECORD,
        NEW RECORD
    )
        RETURNS RECORD AS $$
        DECLARE
            parent_and_grandparent_ids uuid[];
            children_and_grandchildren_ids uuid[];
        BEGIN
            IF OLD IS NULL OR OLD.itemized <> NEW.itemized THEN
                IF NEW.itemized is TRUE THEN
                    parent_and_grandparent_ids :=
                        get_parent_grandparent_transaction_ids(NEW);
                    PERFORM set_itemization_for_ids(TRUE, parent_and_grandparent_ids);
                ELSE
                    children_and_grandchildren_ids :=
                        get_children_and_grandchildren_transaction_ids(NEW);
                    PERFORM set_itemization_for_ids(
                        FALSE,children_and_grandchildren_ids
                    );
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
        )


def calculate_aggregates(apps, schema):
    with connection.cursor() as cursor:
        cursor.execute(
            """
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
        """
        )


def update_can_unamend(apps, schema):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE OR REPLACE FUNCTION update_can_unamend(
                NEW RECORD
            )
            RETURNS RECORD AS $$
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
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0014_drop_transaction_view"),
    ]

    operations = [
        migrations.RunPython(
            drop_old_triggers,
        ),
        migrations.RunPython(
            drop_old_functions,
        ),
        migrations.RunPython(
            process_itemization,
        ),
        migrations.RunPython(
            handle_parent_itemization,
        ),
        migrations.RunPython(
            calculate_aggregates,
        ),
        migrations.RunPython(
            update_can_unamend,
        ),
        migrations.RunPython(
            before_transactions_transaction_insert,
        ),
        migrations.RunPython(
            before_transactions_transaction_update,
        ),
        migrations.RunPython(
            after_transactions_transaction_insert,
        ),
        migrations.RunPython(
            after_transactions_transaction_update,
        ),
        migrations.RunPython(
            create_triggers,
        ),
    ]
