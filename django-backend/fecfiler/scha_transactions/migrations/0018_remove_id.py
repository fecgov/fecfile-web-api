# Generated by Django 3.2.12 on 2022-09-09 16:41

from django.db import migrations, models


def update_uuid(apps, schema_editor):
    SchATransaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa
    transaction_uuid = SchATransaction.objects.filter(
        id=models.OuterRef("parent_transaction_old")
    ).values_list("uuid")[:1]
    SchATransaction.objects.update(parent_transaction=models.Subquery(transaction_uuid))


class Migration(migrations.Migration):

    dependencies = [
        ("scha_transactions", "0017_schatransaction_uuid"),
    ]

    operations = [
        migrations.RenameField(
            model_name="schatransaction",
            old_name="parent_transaction",
            new_name="parent_transaction_old",
        ),
        migrations.AddField(
            model_name="schatransaction",
            name="parent_transaction",
            field=models.ForeignKey(
                null=True,
                on_delete=models.deletion.CASCADE,
                to="self",
            ),
        ),
        migrations.RunPython(update_uuid),
        migrations.RemoveField(
            model_name="schatransaction",
            name="id",
        ),
        migrations.RemoveField(
            model_name="schatransaction",
            name="parent_transaction_old",
        ),
    ]
