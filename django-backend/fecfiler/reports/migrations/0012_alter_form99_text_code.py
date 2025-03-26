from django.db import migrations, models


def copy_text_code_to_text_code_2(apps, schema_editor):
    form_99 = apps.get_model("reports", "Form99")
    for form in form_99.objects.all():
        form.text_code_2 = form.text_code or ""
        form.save(update_fields=["text_code_2"])


def copy_text_code_2_to_text_code(apps, schema_editor):
    form_99 = apps.get_model("reports", "Form99")
    for form in form_99.objects.all():
        form.text_code = form.text_code_2
        form.save(update_fields=["text_code"])


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0011_remove_form3x_cash_on_hand_date"),
    ]

    operations = [
        # Step 1: Add the column as NULLABLE (to prevent NOT NULL constraint errors)
        migrations.AddField(
            model_name="form99",
            name="text_code_2",
            field=models.TextField(),
        ),
        migrations.RunPython(
            copy_text_code_to_text_code_2,
            reverse_code=copy_text_code_2_to_text_code,
        ),
        migrations.RunSQL(
            sql="""
                ALTER TABLE reports_form99 ALTER COLUMN text_code_2 SET NOT NULL;
                ALTER TABLE reports_form99 ALTER COLUMN text_code SET DEFAULT '';
            """,
            reverse_sql="""
                ALTER TABLE reports_form99 ALTER COLUMN text_code_2 DROP NOT NULL;
                ALTER TABLE reports_form99 ALTER COLUMN text_code_2 DROP DEFAULT;
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
