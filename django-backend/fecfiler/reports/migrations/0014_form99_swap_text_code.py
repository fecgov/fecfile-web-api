from django.db import migrations
from django_migration_linter import IgnoreMigration


class Migration(migrations.Migration):

    dependencies = [
        ("reports", "0013_form3_report_form_3"),
    ]

    operations = [
        IgnoreMigration(),
        migrations.RemoveField(model_name="form99", name="text_code"),
        migrations.RenameField(
            model_name="form99", old_name="text_code_2", new_name="text_code"
        ),
    ]
