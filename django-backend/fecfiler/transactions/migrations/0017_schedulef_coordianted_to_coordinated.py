# Generated by Dan 1.0 on 2025-03-17 16:25ish

from django.db import migrations
import django_migration_linter as linter


class Migration(migrations.Migration):
    dependencies = [
        ("transactions", "0016_schedulef_transaction_contact_4_and_more"),
    ]

    operations = [
        linter.IgnoreMigration(),
        migrations.RenameField(
            model_name="schedulef",
            old_name="filer_designated_to_make_coordianted_expenditures",
            new_name="filer_designated_to_make_coordinated_expenditures",
        ),
    ]
