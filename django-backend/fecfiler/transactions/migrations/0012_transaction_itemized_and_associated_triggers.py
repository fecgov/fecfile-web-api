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
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="transaction",
            name="itemized",
            field=models.BooleanField(default=False),
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
                "indexes": [models.Index(fields=["type"])],
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
        CREATE OR REPLACE FUNCTION calculate_itemized()
        RETURNS VOID AS $$
        BEGIN
            IF NEW.force_itemized IS NOT NULL
            THEN
                NEW._itemized := NEW.force_itemized
            ELSIF NEW.aggregate < 0
            THEN
                NEW._itemized := TRUE
            ELSIF EXISTS (
                SELECT type 
                FROM over_two_hundred_types 
                WHERE type = NEW.transaction_type_identifier
            )
            THEN
                NEW._itemized := NEW.aggregate > 200
            ELSE
                NEW._itemized := TRUE
            END IF;
            NEW.itemized = NEW._itemized
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION on_itemized_changed()
        RETURNS VOID AS $$
        DECLARE
            parent_and_grandparent_ids TEXT[];
            children_and_grandchildren_ids TEXT[];
        BEGIN
            parent_and_grandparent_ids := get_parent_grandparent_transaction_ids(NEW)
            children_and_grandchildren_ids := get_children_and_grandchildren_transaction_ids(NEW)
            IF NEW._itemized
            THEN
                UPDATE transactions_transaction
                SET 
                    relationally_itemized_count = NEW.relationally_itemized_count + 1,
                    relationally_unitemized_count = 0,
                    itemized = TRUE
                WHERE id IN (parent_and_grandparent_ids)
                UPDATE transactions_transaction
                SET 
                    relationally_unitemized_count = NEW.relationally_unitemized_count - 1
                WHERE id IN (children_and_grandchildren_ids)
            ELSE
                UPDATE transactions_transaction
                SET 
                    relationally_itemized_count = NEW.relationally_itemized_count - 1
                WHERE id IN (parent_and_grandparent_ids)
                UPDATE transactions_transaction
                SET 
                    relationally_unitemized_count = NEW.relationally_unitemized_count + 1,
                    relationally_itemized_count = 0,
                    itemized = FALSE
                WHERE id IN (children_and_grandchildren_ids)
            END IF;
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION get_parent_grandparent_transaction_ids(
            txn RECORD
        )
        RETURNS text[] AS $$
        BEGIN
            SELECT (
                txn.parent_transaction_id,
                (
                    SELECT parent_transaction_id
                    FROM transactions_transaction
                    WHERE id = txn.parent_transaction_id
                )
            ) into retval
            RETURN retval
        END;
        $$ LANGUAGE plpgsql;

        CREATE OR REPLACE FUNCTION get_children_and_grandchildren_transaction_ids(
            txn RECORD
        )
        RETURNS text[] AS $$
        BEGIN
            SELECT (
                SELECT id
                FROM transactions_transaction
                WHERE parent_transaction_id IN (
                    txn.id,
                    (
                        SELECT id
                        FROM transactions_transaction
                        WHERE parent_transaction_id = txn.id
                    ),
                )
            ) into retval
            RETURN retval
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER calculate_itemized_trigger
        BEFORE INSERT OR UPDATE ON transactions_transaction
        FOR EACH ROW
        WHEN ((pg_trigger_depth() = 0) 
        AND (TG_OP = 'INSERT')
        OR (
            TG_OP = 'UPDATE' 
            AND (
                OLD.force_itemized IS DISTINCT FROM NEW.force_itemized 
                OR OLD.aggregate IS DISTINCT FROM NEW.aggregate
                OR (
                    (
                        OLD.relationally_itemized_count IS DISTINCT FROM NEW.relationally_itemized_count
                        OR OLD.relationally_unitemized_count IS DISTINCT FROM NEW.relationally_unitemized_count
                    )
                    AND OLD.relationally_itemized_count = 0
                    AND OLD.relationally_unitemized_count = 0
                )
            )
        )
        EXECUTE FUNCTION calculate_itemized();

        CREATE TRIGGER on_itemization_change_trigger
        AFTER INSERT OR UPDATE ON transactions_transaction
        FOR EACH ROW
        WHEN (pg_trigger_depth() = 0) -- Prevent infinite trigger loop
        AND (TG_OP = 'INSERT') 
        OR (
            TG_OP = 'UPDATE' AND OLD._itemized != NEW._itemized
        )
        EXECUTE FUNCTION on_itemized_changed();
        """
        ),
    ]
