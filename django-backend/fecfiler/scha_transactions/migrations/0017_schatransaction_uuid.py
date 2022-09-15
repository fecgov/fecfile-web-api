# Generated by Django 3.2.12 on 2022-09-09 16:41

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    def create_uuid(apps, schema_editor):
        SchATransaction = apps.get_model("scha_transactions", "SchATransaction")
        for scha_transaction in SchATransaction.objects.all():
            scha_transaction.uuid = uuid.uuid4()
            scha_transaction.save()

    def update_uuid(apps, schema_editor):
        SchATransaction = apps.get_model("scha_transactions", "SchATransaction")
        transaction_uuid = SchATransaction.objects.filter(
            id=models.OuterRef("parent_transaction_old")
        ).values_list("uuid")[:1]
        SchATransaction.objects.update(
            parent_transaction=models.Subquery(transaction_uuid)
        )

    dependencies = [
        ("scha_transactions", "0016_auto_20220810_0938"),
    ]

    operations = [
        migrations.AddField(
            model_name="schatransaction",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.RunPython(create_uuid),
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
