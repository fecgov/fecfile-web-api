# Generated by Django 3.2.12 on 2022-10-31 14:44

from django.db import migrations


def text_field_to_text_record(apps, _):
    sch_a_transaction = apps.get_model("scha_transactions", "schatransaction")  # noqa
    memo_text = apps.get_model("memo_text", "memotext")
    for transaction in sch_a_transaction.objects.all():
        transaction.memo_text = memo_text()
        transaction.memo_text.text4000 = transaction.memo_text_description
        transaction.memo_text.transaction_id = transaction.id
        transaction.memo_text.save()
        transaction.save()


def text_record_to_text_field(apps, _):
    sch_a_transaction = apps.get_model("scha_transactions", "schatransaction")  # noqa
    memo_text = apps.get_model("memo_text", "memotext")
    for transaction in sch_a_transaction.objects.all():
        record = memo_text.objects.get(id=transaction.memo_text.id)
        text = record.text4000
        transaction.memo_text_description = text
        transaction.memo_text = None
        transaction.save()
        record.delete()
        record.save()


class Migration(migrations.Migration):

    dependencies = [
        ('scha_transactions', '0032_schatransaction_memo_text'),
    ]

    operations = [
        migrations.RunPython(text_field_to_text_record, text_record_to_text_field),
    ]
