# Generated migration for performance optimization
# Adds indexes to support cascade and aggregate queries

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0025_alter_transaction_itemized'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(
                fields=['parent_transaction_id', 'deleted'],
                name='txn_parent_deleted_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(
                fields=['contact_1_id', 'aggregation_group', 'deleted'],
                name='txn_entity_agg_idx'
            ),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(
                fields=['deleted'],
                name='txn_deleted_idx'
            ),
        ),
    ]
