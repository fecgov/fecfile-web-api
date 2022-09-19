# Generated by Django 3.2.12 on 2022-09-09 16:41

from django.db import migrations, models
import uuid


def create_uuid(apps, schema_editor):
    SchATransaction = apps.get_model("scha_transactions", "SchATransaction")  # noqa
    for scha_transaction in SchATransaction.objects.all():
        scha_transaction.uuid = uuid.uuid4()
        scha_transaction.save()


def noop():
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("scha_transactions", "0016_auto_20220810_0938"),
    ]

    operations = [
        migrations.AddField(
            model_name="schatransaction",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.RunPython(create_uuid, noop),
        migrations.AlterField(
            model_name="schatransaction",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name="schatransaction",
            name="parent_transaction",
            field=models.IntegerField(null=True),
        ),
        migrations.AlterField(
            model_name="schatransaction",
            name="id",
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name="schatransaction",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
                unique=True,
            ),
        ),
    ]
