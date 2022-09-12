# Generated by Django 3.2.12 on 2022-09-12 20:34

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    def create_uuid(apps, schema_editor):
        MemoText = apps.get_model("memo_text", "MemoText")
        for memo_text in MemoText.objects.all():
            memo_text.uuid = uuid.uuid4()
            memo_text.save()

    dependencies = [
        ("memo_text", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="memotext",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.RunPython(create_uuid),
        migrations.AlterField(
            model_name="memotext",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
