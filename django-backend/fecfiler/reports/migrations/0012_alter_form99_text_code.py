from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0011_remove_form3x_cash_on_hand_date"),
    ]

    operations = [
        # Step 1: Add the column as NULLABLE (to prevent NOT NULL constraint errors)
        migrations.AddField(
            model_name="form99",
            name="text_code_2",
            field=models.TextField(db_default=""),
        ),
        migrations.RunSQL(
            sql="""
                UPDATE reports_form99 SET text_code_2 = COALESCE(text_code, '');
                ALTER TABLE reports_form99 ALTER COLUMN text_code SET DEFAULT '';
                ALTER TABLE reports_form99 ALTER COLUMN text_code_2 SET NOT NULL;
            """,
            reverse_sql="""
                ALTER TABLE reports_form99 ALTER COLUMN text_code_2 DROP DEFAULT;
                ALTER TABLE reports_form99 ALTER COLUMN text_code_2 DROP NOT NULL;
            """,
            state_operations=[
                migrations.AlterField(
                    model_name="form99",
                    name="text_code_2",
                    field=models.TextField(
                        null=False, blank=False, default="", db_default=""
                    ),
                ),
            ],
        ),
    ]
