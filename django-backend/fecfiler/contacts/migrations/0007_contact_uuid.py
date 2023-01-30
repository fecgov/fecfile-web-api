# Generated by Django 3.2.12 on 2022-09-09 16:41

from django.db import migrations, models
import uuid


def create_uuid(apps, schema_editor):
    Contact = apps.get_model("contacts", "Contact")  # noqa
    for contact in Contact.objects.all():
        contact.uuid = uuid.uuid4()
        contact.save()


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0006_alter_contact_committee_account"),
    ]

    operations = [
        migrations.AddField(
            model_name="contact",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, null=True),
        ),
        migrations.RunPython(create_uuid, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="contact",
            name="uuid",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name="contact",
            name="id",
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name="contact",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True
            ),
        ),
        migrations.RemoveField(model_name="contact", name="id"),
    ]
