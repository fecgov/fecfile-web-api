# Generated by Django 3.2.12 on 2022-09-15 17:09

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0009_committee_uuid_fk"),
    ]

    operations = [
        migrations.RenameField(
            model_name="contact",
            old_name="uuid",
            new_name="id",
        ),
    ]
