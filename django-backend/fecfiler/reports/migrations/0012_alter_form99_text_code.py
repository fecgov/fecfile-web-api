from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0011_remove_form3x_cash_on_hand_date"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE reports_form99 ALTER COLUMN text_code SET DEFAULT '';",
            reverse_sql="ALTER TABLE reports_form99 ALTER COLUMN text_code DROP DEFAULT;",
            state_operations=[
                migrations.AlterField(
                    model_name="form99",
                    name="text_code",
                    field=models.TextField(null=False, blank=False, default=""),
                ),
            ],
        ),
    ]
