# Generated by Django 3.2.12 on 2022-09-12 20:34

from django.db import migrations, models
import uuid


def create_uuid(apps, schema_editor):
    MemoText = apps.get_model("memo_text", "MemoText")  # noqa
    for memo_text in MemoText.objects.all():
        memo_text.uuid = uuid.uuid4()
        memo_text.save()


def noop():
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("memo_text", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="memotext",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.RunPython(create_uuid, noop),
        migrations.AlterField(
            model_name="memotext",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name="memotext",
            name="id",
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name="memotext",
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
