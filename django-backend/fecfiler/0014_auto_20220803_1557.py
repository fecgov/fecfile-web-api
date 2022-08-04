# Generated by Django 3.2.12 on 2022-08-03 19:57

from django.db import migrations, models
import uuid

def convert_id_to_uuid(apps, schema_editor):

    SchATransaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa

    for transaction in SchATransaction.objects.all():
        old_id = transaction.id
        transaction.id = uuid.uuid4();
        transaction.save()
        for child_transaction in SchATransaction.objects.all():
            if (child_transaction.parent_transaction_id == old_id):
                child_transaction.parent_transaction = transaction
                child_transaction.save()


class Migration(migrations.Migration):

    dependencies = [
        ('scha_transactions', '0013_auto_20220725_0232'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='schatransaction',
            name='transaction_id',
        ),
        migrations.AlterField(
            model_name='schatransaction',
            name='id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.RunPython(convert_id_to_uuid),
    ]
