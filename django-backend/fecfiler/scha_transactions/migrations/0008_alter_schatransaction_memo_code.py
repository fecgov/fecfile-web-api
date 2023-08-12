# Generated by Django 3.2.12 on 2022-05-16 11:44

from django.db import migrations, models


def convert_fecfile_booleans(apps, schema_editor):

    SchATransaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa

    for transaction in SchATransaction.objects.all():
        transaction.memo_code = (
            True if transaction.memo_code in ["true", "X"] else False
        )
        transaction.save()


class Migration(migrations.Migration):

    dependencies = [
        ("scha_transactions", "0007_alter_schatransaction_committee_account"),
    ]

    operations = [
        migrations.RunPython(convert_fecfile_booleans),
        migrations.AlterField(
            model_name="schatransaction",
            name="memo_code",
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]