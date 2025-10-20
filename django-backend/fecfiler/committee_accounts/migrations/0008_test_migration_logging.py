from django.db import migrations
import structlog

logger = structlog.get_logger(__name__)


def test_migration_logging(apps, schema_editor):
    logger.info("====== testing migration logging 1 ======")
    logger.info("====== testing migration logging 2 ======")
    logger.info("====== testing migration logging 3 ======")


class Migration(migrations.Migration):

    dependencies = [
        ("committee_accounts", "0007_alter_committeeaccount_members"),
    ]

    operations = [
        migrations.RunPython(
            test_migration_logging, reverse_code=migrations.RunPython.noop
        ),
    ]
