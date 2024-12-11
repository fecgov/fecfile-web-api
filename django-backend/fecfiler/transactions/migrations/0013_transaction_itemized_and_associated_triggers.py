from django.db import migrations, models
from fecfiler.transactions.schedule_a.managers import (
    over_two_hundred_types as schedule_a_over_two_hundred_types,
)
from fecfiler.transactions.schedule_b.managers import (
    over_two_hundred_types as schedule_b_over_two_hundred_types,
)
from ..models import OverTwoHundredTypes
import uuid


def populate_over_two_hundred_types(apps, schema_editor):
    scha_types_to_create = [
        OverTwoHundredTypes(type=type_to_create)
        for type_to_create in schedule_a_over_two_hundred_types
    ]
    schb_types_to_create = [
        OverTwoHundredTypes(type=type_to_create)
        for type_to_create in schedule_b_over_two_hundred_types
    ]
    OverTwoHundredTypes.objects.bulk_create(scha_types_to_create + schb_types_to_create)


class Migration(migrations.Migration):

    dependencies = [
        ("transactions", "0012_alter_transactions_blocking_reports"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="_itemized",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="transaction",
            name="itemized",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="transaction",
            name="relationally_itemized_count",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="transaction",
            name="relationally_unitemized_count",
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name="OverTwoHundredTypes",
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
                "db_table": "over_two_hundred_types",
                "indexes": [
                    models.Index(fields=["type"], name="over_two_hu_type_21f14e_idx")
                ],
            },
        ),
        migrations.RunSQL(
            """
            CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        """
        ),
        migrations.RunPython(populate_over_two_hundred_types),
        migrations.RunSQL(
            """
        CREATE OR REPLACE FUNCTION before_transactions_transaction_insert_or_update()
        RETURNS TRIGGER AS $$
        DECLARE
            needs_internal_itemized_set boolean;
            needs_relational_itemized_set boolean;
            internal_itemization boolean;
            relational_itemization boolean;
        BEGIN
            needs_internal_itemized_set := needs_internal_itemized_set(OLD, NEW);
            IF needs_internal_itemized_set THEN
                NEW._itemized := calculate_internal_itemization(NEW);
            END IF;

            needs_relational_itemized_set := needs_relational_itemized_set(OLD, NEW);
            IF needs_relational_itemized_set THEN
                NEW.itemized := calculate_relational_itemization(NEW);
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION needs_internal_itemized_set(
            OLD RECORD,
            NEW RECORD
        )
        RETURNS BOOLEAN AS $$
        BEGIN
            return OLD IS NULL OR (
                OLD.force_itemized IS DISTINCT FROM NEW.force_itemized
                OR OLD.aggregate IS DISTINCT FROM NEW.aggregate
                OR (
                    (
                        OLD.relationally_itemized_count <>
                            NEW.relationally_itemized_count
                        OR OLD.relationally_unitemized_count <>
                            NEW.relationally_unitemized_count
                    )
                    AND NEW.relationally_itemized_count = 0
                    AND NEW.relationally_unitemized_count = 0
                )
            );
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION calculate_internal_itemization(
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
                SELECT type
                FROM over_two_hundred_types
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

        CREATE OR REPLACE FUNCTION needs_relational_itemized_set(
            OLD RECORD,
            NEW RECORD
        )
        RETURNS BOOLEAN AS $$
        BEGIN
            return OLD IS NULL OR (
                OLD.relationally_itemized_count IS DISTINCT FROM
                    NEW.relationally_itemized_count
                OR OLD.relationally_unitemized_count IS DISTINCT FROM
                    NEW.relationally_unitemized_count
            );
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION calculate_relational_itemization(
            txn RECORD
        )
        RETURNS BOOLEAN AS $$
        BEGIN
            IF txn.relationally_itemized_count > 0 THEN
                return TRUE;
            ELSIF txn.relationally_unitemized_count > 0 THEN
                return FALSE;
            END IF;
            return txn._itemized;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION after_transactions_transaction_insert_or_update()
        RETURNS TRIGGER AS $$
        DECLARE
            needs_internal_itemized_set boolean;
        BEGIN
            IF (TG_OP = 'INSERT') THEN
                PERFORM after_transactions_transaction_insert(NEW);
            ELSIF (TG_OP = 'UPDATE') THEN
                needs_internal_itemized_set := needs_internal_itemized_set(OLD, NEW);
                IF needs_internal_itemized_set = TRUE THEN
                    PERFORM after_transactions_transaction_internal_itemized_update(NEW);
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION after_transactions_transaction_insert(
            txn RECORD
        )
        RETURNS VOID AS $$
        DECLARE
            parent_and_grandparent_ids uuid[];
            parent_itemized_flag boolean;
        BEGIN
            IF txn._itemized THEN
                parent_and_grandparent_ids := get_parent_grandparent_transaction_ids(txn);
                PERFORM relational_itemize_ids(parent_and_grandparent_ids);
            ELSIF txn.parent_transaction_id IS NOT NULL THEN
                SELECT itemized
                INTO parent_itemized_flag
                FROM transactions_transaction
                WHERE id = txn.parent_transaction_id;
                IF parent_itemized_flag IS FALSE THEN
                    PERFORM relational_unitemize_ids(ARRAY[txn.id]); 
                END IF;
            END IF;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION after_transactions_transaction_internal_itemized_update(
            txn RECORD
        )
        RETURNS VOID AS $$
        DECLARE
            parent_and_grandparent_ids uuid[];
            parent_or_grandparent_children_and_grandchildren_ids uuid[];
            children_and_grandchildren_ids uuid[];
        BEGIN
            IF txn._itemized THEN
                parent_and_grandparent_ids := get_parent_grandparent_transaction_ids(txn);
                PERFORM relational_itemize_ids(parent_and_grandparent_ids);
                parent_or_grandparent_children_and_grandchildren_ids :=
                    get_children_and_grandchildren_transaction_ids(
                        parent_and_grandparent_ids[
                            cardinality(parent_and_grandparent_ids)
                        ]
                    );
                PERFORM undo_relational_unitemize_ids(
                    parent_or_grandparent_children_and_grandchildren_ids
                );
            ELSE
                children_and_grandchildren_ids :=
                    get_children_and_grandchildren_transaction_ids(txn.id);
                PERFORM relational_unitemize_ids(children_and_grandchildren_ids);
                parent_and_grandparent_ids := get_parent_grandparent_transaction_ids(txn);
                PERFORM undo_relational_itemize_ids(parent_and_grandparent_ids);
            END IF;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION after_transactions_transaction_delete()
        RETURNS TRIGGER AS $$
        DECLARE
            parent_and_grandparent_ids uuid[];
            children_and_grandchildren_ids uuid[];
        BEGIN
            IF OLD._itemized THEN
                parent_and_grandparent_ids := get_parent_grandparent_transaction_ids(txn);
                PERFORM undo_relational_itemize_ids(OLD);
            ELSE
                children_and_grandchildren_ids :=
                    get_children_and_grandchildren_transaction_ids(OLD.id);
                PERFORM undo_relational_unitemize_ids(
                    children_and_grandchildren_ids
                );
            END IF;
            RETURN OLD;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION relational_itemize_ids(
            ids uuid[]
        )
        RETURNS VOID AS $$
        BEGIN
            IF cardinality(ids) > 0 THEN
                UPDATE transactions_transaction
                SET
                    relationally_itemized_count = relationally_itemized_count + 1,
                    relationally_unitemized_count = 0
                WHERE id = ANY (ids);
            END IF;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION undo_relational_itemize_ids(
            ids uuid[]
        )
        RETURNS VOID AS $$
        BEGIN
            IF cardinality(ids) > 0 THEN
                UPDATE transactions_transaction
                SET
                    relationally_itemized_count = relationally_itemized_count - 1
                WHERE id = ANY (ids);
            END IF;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION relational_unitemize_ids(
            ids uuid[]
        )
        RETURNS VOID AS $$
        BEGIN
            IF cardinality(ids) > 0 THEN
                UPDATE transactions_transaction
                SET
                    relationally_unitemized_count = 1,
                    relationally_itemized_count = 0
                WHERE id = ANY (ids);
            END IF;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION undo_relational_unitemize_ids(
            ids uuid[]
        )
        RETURNS VOID AS $$
        BEGIN
            IF cardinality(ids) > 0 THEN
                UPDATE transactions_transaction
                SET
                    relationally_unitemized_count = 0
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
            txn_id uuid
        )
        RETURNS uuid[] AS $$
        DECLARE
            ids uuid[];
        BEGIN
            SELECT array(
                SELECT id
                FROM transactions_transaction
                WHERE parent_transaction_id = ANY (
                    array_prepend(txn_id,
                        array(
                            SELECT id
                            FROM transactions_transaction
                            WHERE parent_transaction_id = txn_id
                        )
                    )
                )
            ) into ids;
            RETURN ids;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER zbefore_transactions_transaction_insert_or_update_trigger
        BEFORE INSERT OR UPDATE ON transactions_transaction
        FOR EACH ROW
        EXECUTE FUNCTION before_transactions_transaction_insert_or_update();

        CREATE TRIGGER zafter_transactions_transaction_insert_or_update_trigger
        AFTER INSERT OR UPDATE ON transactions_transaction
        FOR EACH ROW
        WHEN (pg_trigger_depth() = 0) -- Prevent infinite trigger loop
        EXECUTE FUNCTION after_transactions_transaction_insert_or_update();

        CREATE TRIGGER zafter_transactions_transaction_delete_trigger
        AFTER DELETE ON transactions_transaction
        FOR EACH ROW
        EXECUTE FUNCTION after_transactions_transaction_delete();
        """
        ),
    ]
