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
        ("transactions", "0011_transaction_can_delete"),
    ]

    operations = [
        migrations.AddField(
            model_name="transaction",
            name="_itemized",
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
                NEW.itemized := NEW.force_itemized
            ELSIF NEW.aggregate < 0
            THEN
                NEW.itemized := TRUE
            NEW.
            END IF;
            NEW.itemized := TRUE
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER calculate_itemized_insert_trigger
        BEFORE INSERT ON transactions_transaction
        FOR EACH ROW
        WHEN (pg_trigger_depth() = 0) -- Prevent infinite trigger loop
        EXECUTE FUNCTION calculate_itemized();

        CREATE TRIGGER calculate_itemized_update_trigger
        BEFORE UPDATE ON transactions_transaction
        FOR EACH ROW
        WHEN ((pg_trigger_depth() = 0) 
        AND (OLD.force_itemized IS DISTINCT FROM NEW.force_itemized 
            OR OLD.aggregate IS DISTINCT FROM NEW.aggregate))
        EXECUTE FUNCTION calculate_itemized();
        """
        ),
    ]
