from django.db import connection, migrations, models
from fecfiler.transactions.schedule_a.managers import (
    over_two_hundred_types as schedule_a_over_two_hundred_types,
)
from fecfiler.transactions.schedule_b.managers import (
    over_two_hundred_types as schedule_b_over_two_hundred_types,
)
import uuid


def populate_over_two_hundred_types(apps, schema_editor):
    OverTwoHundredTypesScheduleA = apps.get_model(  # noqa: N806
        "transactions", "OverTwoHundredTypesScheduleA"
    )
    OverTwoHundredTypesScheduleB = apps.get_model(  # noqa: N806
        "transactions", "OverTwoHundredTypesScheduleB"
    )
    scha_types_to_create = [
        OverTwoHundredTypesScheduleA(type=type_to_create)
        for type_to_create in schedule_a_over_two_hundred_types
    ]
    OverTwoHundredTypesScheduleA.objects.bulk_create(scha_types_to_create)
    schb_types_to_create = [
        OverTwoHundredTypesScheduleB(type=type_to_create)
        for type_to_create in schedule_b_over_two_hundred_types
    ]
    OverTwoHundredTypesScheduleB.objects.bulk_create(schb_types_to_create)


def drop_over_two_hundred_types(apps, schema_editor):
    print("this reverses migration automatically.")


def create_itemized_triggers_and_functions(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute(
            """
        CREATE OR REPLACE FUNCTION before_transactions_transaction_insert_or_update()
        RETURNS TRIGGER AS $$
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

        CREATE OR REPLACE FUNCTION calculate_itemization(
            txn RECORD
        )
        RETURNS BOOLEAN AS $$
        DECLARE
            itemized boolean;
        BEGIN
            itemized := TRUE;
            IF txn.force_itemized IS NOT NULL THEN
                itemized := txn.force_itemized;
            ELSIF txn.aggregate < 0 THEN
                itemized := TRUE;
            ELSIF EXISTS (
                SELECT type from (
                    SELECT type
                    FROM over_two_hundred_types_schedulea
                    UNION
                    SELECT type
                    FROM over_two_hundred_types_scheduleb
                ) as scha_schb_types
                WHERE type = txn.transaction_type_identifier
            ) THEN
                IF txn.aggregate > 200 THEN
                    itemized := TRUE;
                ELSE
                    itemized := FALSE;
                END IF;
            END IF;
            return itemized;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION after_transactions_transaction_insert_or_update()
        RETURNS TRIGGER AS $$
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

        CREATE OR REPLACE FUNCTION needs_itemized_set(
            OLD RECORD,
            NEW RECORD
        )
        RETURNS BOOLEAN AS $$
        BEGIN
            return OLD IS NULL OR (
                OLD.force_itemized IS DISTINCT FROM NEW.force_itemized
                OR OLD.aggregate IS DISTINCT FROM NEW.aggregate
            );
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION set_itemization_for_ids(
            itemization boolean,
            ids uuid[]
        )
        RETURNS VOID AS $$
        BEGIN
            IF cardinality(ids) > 0 THEN
                UPDATE transactions_transaction
                SET
                    itemized = itemization
                WHERE id = ANY (ids);
            END IF;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION get_parent_grandparent_transaction_ids(
            txn RECORD
        )
        RETURNS uuid[] AS $$
        DECLARE
            ids uuid[];
        BEGIN
            SELECT array(
                SELECT id
                FROM transactions_transaction
                WHERE id IN (
                    txn.parent_transaction_id,
                    (
                        SELECT parent_transaction_id
                        FROM transactions_transaction
                        WHERE id = txn.parent_transaction_id
                    )
                )
            ) into ids;
            RETURN ids;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION get_children_and_grandchildren_transaction_ids(
            txn RECORD
        )
        RETURNS uuid[] AS $$
        DECLARE
            ids uuid[];
        BEGIN
            SELECT array(
                SELECT id
                FROM transactions_transaction
                WHERE parent_transaction_id = ANY (
                    array_prepend(txn.id,
                        array(
                            SELECT id
                            FROM transactions_transaction
                            WHERE parent_transaction_id = txn.id
                        )
                    )
                )
            ) into ids;
            RETURN ids;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER before_transactions_transaction_insert_or_update_trigger
        BEFORE INSERT OR UPDATE ON transactions_transaction
        FOR EACH ROW
        EXECUTE FUNCTION before_transactions_transaction_insert_or_update();

        CREATE TRIGGER zafter_transactions_transaction_insert_or_update_trigger
        AFTER INSERT OR UPDATE ON transactions_transaction
        FOR EACH ROW
        EXECUTE FUNCTION after_transactions_transaction_insert_or_update();
        """
        )


def drop_itemized_triggers_and_functions(apps, schema_editor):
    schema_editor.execute(
        """
        DROP TRIGGER
        IF EXISTS zafter_transactions_transaction_insert_or_update_trigger
        ON transactions_transaction;

        DROP TRIGGER
        IF EXISTS before_transactions_transaction_insert_or_update_trigger
        ON transactions_transaction;

        DROP FUNCTION IF EXISTS before_transactions_transaction_insert_or_update;
        DROP FUNCTION IF EXISTS calculate_itemization;
        DROP FUNCTION IF EXISTS after_transactions_transaction_insert_or_update;
        DROP FUNCTION IF EXISTS needs_itemized_set;
        DROP FUNCTION IF EXISTS set_itemization_for_ids;
        DROP FUNCTION IF EXISTS get_parent_grandparent_transaction_ids;
        DROP FUNCTION IF EXISTS get_children_and_grandchildren_transaction_ids;
        """
    )


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0012_alter_transactions_blocking_reports"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="itemized",
            field=models.BooleanField(db_default=True),
        ),
        migrations.CreateModel(
            name="OverTwoHundredTypesScheduleA",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("type", models.TextField()),
            ],
            options={
                "db_table": "over_two_hundred_types_schedulea",
                "indexes": [
                    models.Index(fields=["type"], name="over_two_hu_type_2c8314_idx")
                ],
            },
        ),
        migrations.CreateModel(
            name="OverTwoHundredTypesScheduleB",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("type", models.TextField()),
            ],
            options={
                "db_table": "over_two_hundred_types_scheduleb",
                "indexes": [
                    models.Index(fields=["type"], name="over_two_hu_type_411a44_idx")
                ],
            },
        ),
        migrations.RunPython(
            populate_over_two_hundred_types,
            reverse_code=drop_over_two_hundred_types,
        ),
        migrations.RunPython(
            create_itemized_triggers_and_functions,
            reverse_code=drop_itemized_triggers_and_functions,
        ),
    ]
