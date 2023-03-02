# Generated by Django 3.2.12 on 2022-08-04 18:49

from django.db import migrations, models
import uuid


def check_for_uid_conflicts(apps, uid):
    scha_transaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa
    return len(scha_transaction.objects.filter(transaction_id=uid)) > 0


def generate_uid():
    unique_id = uuid.uuid4()
    hex_id = unique_id.hex.upper()
    return hex_id[-21] + hex_id[-19:]


def generate_uids(apps, schema_editor):
    scha_transaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa
    for transaction in scha_transaction.objects.all():
        unique_id = generate_uid()

        attempts = 0
        while check_for_uid_conflicts(apps, unique_id):
            unique_id = generate_uid()
            attempts += 1
            if (attempts > 5):
                print("Unique ID generation failed: Over 5 conflicts in a row")
                return

        transaction.transaction_id = unique_id
        transaction.save()


class Migration(migrations.Migration):

    dependencies = [
        ('scha_transactions', '0013_auto_20220725_0232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='schatransaction',
            name='transaction_id',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RunPython(code=generate_uids, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='schatransaction',
            name='transaction_id',
            field=models.TextField(
                editable=False,
                blank=False,
                null=True,
                max_length=20
            ),
        ),
        migrations.AddIndex(
            model_name='schatransaction',
            index=models.Index(
                fields=['transaction_id'],
                name='scha_trans_transaction_id'
            ),
        ),
    ]